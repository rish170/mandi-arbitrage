import asyncio
from datetime import datetime, timezone
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from cachetools import TTLCache
import httpx
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.geo import estimate_duration_minutes, haversine_fallback_distance_km
from app.models import DistanceCache

logger = logging.getLogger(__name__)

# In-memory TTL cache for distances: up to 10,000 entries, TTL 30 days (2,592,000s)
MEMORY_DISTANCE_CACHE: TTLCache = TTLCache(maxsize=10000, ttl=2592000)

class DistanceResult(BaseModel):
    mandi_id: int
    road_km: float
    duration_min: float
    source: str  # "routes_api" | "haversine_fallback"
    cache_hit: bool = False

def parse_duration_seconds(duration_str: str) -> float:
    """Parse Google Routes API duration format (e.g. '123s' or '3600.5s') to seconds."""
    if not duration_str:
        return 0.0
    clean = duration_str.rstrip("s").strip()
    try:
        return float(clean)
    except ValueError:
        return 0.0

class DistanceService:
    _circuit_breaker_disabled_until: float = 0.0

    def __init__(self, google_api_key: Optional[str] = None, timeout: float = 1.2):
        self.google_api_key = google_api_key or settings.GOOGLE_MAPS_API_KEY
        self.timeout = timeout
        if google_api_key == "TEST_KEY":
            DistanceService._circuit_breaker_disabled_until = 0.0

    async def get_distances(
        self,
        db: AsyncSession,
        origin_lat: float,
        origin_lng: float,
        origin_key: str,
        destinations: List[Tuple[int, float, float]],  # List of (mandi_id, lat, lng)
    ) -> Tuple[Dict[int, DistanceResult], bool]:
        """
        Batched road distance and travel time calculation.
        Checks in-memory cache -> DB DistanceCache -> Google Routes API.
        Falls back to haversine * 1.3 if API call fails or times out.
        Returns:
            distances: Dict[mandi_id, DistanceResult]
            has_fallback: bool (True if any distance used haversine_fallback)
        """
        results: Dict[int, DistanceResult] = {}
        missing_dests: List[Tuple[int, float, float]] = []
        has_fallback = False

        # 1. Check in-memory cache
        for mandi_id, lat, lng in destinations:
            cache_key = f"{origin_key}:{mandi_id}"
            if cache_key in MEMORY_DISTANCE_CACHE:
                cached = MEMORY_DISTANCE_CACHE[cache_key]
                results[mandi_id] = DistanceResult(
                    mandi_id=mandi_id,
                    road_km=cached.road_km,
                    duration_min=cached.duration_min,
                    source=cached.source,
                    cache_hit=True,
                )
            else:
                missing_dests.append((mandi_id, lat, lng))

        # 2. Check DB DistanceCache for missing items
        if missing_dests:
            mandi_ids_to_query = [m[0] for m in missing_dests]
            stmt = select(DistanceCache).where(
                DistanceCache.origin_key == origin_key,
                DistanceCache.mandi_id.in_(mandi_ids_to_query),
            )
            db_res = (await db.execute(stmt)).scalars().all()
            db_cached_ids = set()
            for row in db_res:
                db_cached_ids.add(row.mandi_id)
                res = DistanceResult(
                    mandi_id=row.mandi_id,
                    road_km=row.road_km,
                    duration_min=row.duration_min,
                    source=row.source,
                    cache_hit=True,
                )
                results[row.mandi_id] = res
                MEMORY_DISTANCE_CACHE[f"{origin_key}:{row.mandi_id}"] = res

            missing_dests = [m for m in missing_dests if m[0] not in db_cached_ids]

        # 3. If there are still missing destinations, call Google Routes API
        if missing_dests:
            routes_success = False
            import time
            if self.google_api_key and time.time() >= DistanceService._circuit_breaker_disabled_until:
                if not hasattr(DistanceService, "_lock") or DistanceService._lock is None:
                    DistanceService._lock = asyncio.Lock()
                async with DistanceService._lock:
                    if time.time() >= DistanceService._circuit_breaker_disabled_until:
                        try:
                            routes_results = await self._call_routes_matrix(
                                origin_lat, origin_lng, missing_dests
                            )
                            if routes_results:
                                for mandi_id, res in routes_results.items():
                                    results[mandi_id] = res
                                    MEMORY_DISTANCE_CACHE[f"{origin_key}:{mandi_id}"] = res
                                    # Persist to DB DistanceCache
                                    db.add(
                                        DistanceCache(
                                            origin_key=origin_key,
                                            mandi_id=mandi_id,
                                            road_km=res.road_km,
                                            duration_min=res.duration_min,
                                            source=res.source,
                                        )
                                    )
                                await db.commit()
                                routes_success = True
                        except Exception as e:
                            logger.warning(
                                f"Google Routes API call failed ({type(e).__name__}: {e}). Using haversine fallback."
                            )

            # 4. Fallback to haversine for any remaining missing destinations
            for mandi_id, lat, lng in missing_dests:
                if mandi_id not in results:
                    has_fallback = True
                    road_km = haversine_fallback_distance_km(
                        origin_lat, origin_lng, lat, lng, road_factor=1.3
                    )
                    duration_min = estimate_duration_minutes(road_km, average_speed_kmh=40.0)
                    fallback_res = DistanceResult(
                        mandi_id=mandi_id,
                        road_km=round(road_km, 2),
                        duration_min=round(duration_min, 1),
                        source="haversine_fallback",
                        cache_hit=False,
                    )
                    results[mandi_id] = fallback_res
                    MEMORY_DISTANCE_CACHE[f"{origin_key}:{mandi_id}"] = fallback_res

        # Check if any result in the response used fallback
        for r in results.values():
            if r.source == "haversine_fallback":
                has_fallback = True
                break

        return results, has_fallback

    async def _call_routes_matrix(
        self,
        origin_lat: float,
        origin_lng: float,
        destinations: List[Tuple[int, float, float]],
    ) -> Dict[int, DistanceResult]:
        url = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
        headers = {
            "X-Goog-Api-Key": self.google_api_key,
            "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,status,condition",
            "Content-Type": "application/json",
        }
        body = {
            "origins": [
                {
                    "waypoint": {
                        "location": {
                            "latLng": {
                                "latitude": origin_lat,
                                "longitude": origin_lng,
                            }
                        }
                    }
                }
            ],
            "destinations": [
                {
                    "waypoint": {
                        "location": {
                            "latLng": {
                                "latitude": d[1],
                                "longitude": d[2],
                            }
                        }
                    }
                }
                for d in destinations
            ],
            "travelMode": "DRIVE",
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout, connect=0.6)) as client:
                resp = await asyncio.wait_for(
                    client.post(url, json=body, headers=headers),
                    timeout=self.timeout,
                )
                if resp.status_code != 200:
                    logger.warning(f"Google Routes API HTTP {resp.status_code}: {resp.text[:200]}")
                    if resp.status_code == 403:
                        import time
                        DistanceService._circuit_breaker_disabled_until = time.time() + 60.0
                    return {}

                elements = self._parse_routes_response(resp.text)
                if not elements:
                    return {}

                out: Dict[int, DistanceResult] = {}
                for item in elements:
                    # Handle per-element failures
                    status_obj = item.get("status")
                    if status_obj and isinstance(status_obj, dict) and status_obj.get("code", 0) != 0:
                        continue
                    condition = item.get("condition")
                    if condition == "ROUTE_NOT_FOUND":
                        continue

                    dest_idx = item.get("destinationIndex")
                    if dest_idx is not None and 0 <= dest_idx < len(destinations):
                        mandi_id = destinations[dest_idx][0]
                        dist_meters = item.get("distanceMeters")
                        duration_str = item.get("duration", "0s")
                        if dist_meters is not None:
                            road_km = dist_meters / 1000.0
                            dur_sec = parse_duration_seconds(duration_str)
                            dur_min = dur_sec / 60.0
                            out[mandi_id] = DistanceResult(
                                mandi_id=mandi_id,
                                road_km=round(road_km, 2),
                                duration_min=round(dur_min, 1),
                                source="routes_api",
                                cache_hit=False,
                            )

                return out
        except (asyncio.TimeoutError, httpx.TimeoutException):
            logger.warning(f"Google Routes API timed out after {self.timeout}s. Using haversine fallback.")
            return {}
        except Exception as e:
            logger.warning(f"Google Routes API exception ({type(e).__name__}): {e}")
            return {}

    def _parse_routes_response(self, text: str) -> List[Dict[str, Any]]:
        """Parse Google Routes API response, supporting JSON array or streamed JSON objects."""
        text = text.strip()
        if not text:
            return []
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return [data]
        except Exception:
            pass

        # Fallback to streaming raw decoder
        decoder = json.JSONDecoder()
        results: List[Dict[str, Any]] = []
        idx = 0
        while idx < len(text):
            while idx < len(text) and text[idx] in " \t\r\n,[]":
                idx += 1
            if idx >= len(text):
                break
            try:
                obj, end_idx = decoder.raw_decode(text, idx)
                if isinstance(obj, dict):
                    results.append(obj)
                idx = end_idx
            except Exception:
                break
        return results
