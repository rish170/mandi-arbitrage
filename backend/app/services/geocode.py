import asyncio
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, Optional, Tuple

from cachetools import TTLCache
from fastapi import HTTPException
import httpx
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import GeocodeCache

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
BOUNDS_FILE = CONFIG_DIR / "state_bounds.json"

class GeocodeResult(BaseModel):
    lat: float
    lng: float
    label: str
    source: str  # "google" | "nominatim"
    confidence: float
    is_valid_bound: bool
    needs_review: bool
    cache_hit: bool = False

def load_state_bounds() -> Dict[str, Dict[str, float]]:
    if not BOUNDS_FILE.exists():
        return {}
    with open(BOUNDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

STATE_BOUNDS = load_state_bounds()

def is_within_state_bounds(lat: float, lng: float, state: str) -> bool:
    bounds = STATE_BOUNDS.get(state)
    if not bounds:
        return True
    return (
        bounds["min_lat"] <= lat <= bounds["max_lat"]
        and bounds["min_lng"] <= lng <= bounds["max_lng"]
    )

# In-memory TTL cache for geocoding (24 hours TTL, up to 2000 entries)
MEMORY_GEOCODE_CACHE: TTLCache = TTLCache(maxsize=2000, ttl=86400)
_last_nominatim_time: float = 0.0

class GeocodingService:
    def __init__(self, google_api_key: Optional[str] = None):
        self.google_api_key = google_api_key or settings.GOOGLE_MAPS_API_KEY

    async def resolve_location(
        self,
        db: AsyncSession,
        pincode: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> GeocodeResult:
        """
        Resolve user location from pincode OR (state + district).
        Checks in-memory cache -> DB GeocodeCache -> Google Geocoding -> Nominatim fallback.
        Raises HTTP 422 if location cannot be resolved.
        """
        if pincode:
            cache_key = f"pincode:{pincode.strip()}"
            display_query = f"Pincode {pincode.strip()}"
            google_params = {
                "components": f"postal_code:{pincode.strip()}|country:IN",
                "key": self.google_api_key,
            }
            nominatim_queries = [
                f"{pincode.strip()}, India",
            ]
        elif state and district:
            cache_key = f"district:{state.lower().strip()}:{district.lower().strip()}"
            display_query = f"{district.strip()}, {state.strip()}"
            google_params = {
                "address": f"{district.strip()}, {state.strip()}, India",
                "key": self.google_api_key,
            }
            nominatim_queries = [
                f"{district.strip()}, {state.strip()}, India",
                f"{district.strip()}, India",
            ]
        else:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "MISSING_LOCATION",
                    "message": "Either a 6-digit pincode or state and district must be provided.",
                },
            )

        # 1. Check in-memory cache
        if cache_key in MEMORY_GEOCODE_CACHE:
            cached = MEMORY_GEOCODE_CACHE[cache_key]
            return GeocodeResult(
                lat=cached.lat,
                lng=cached.lng,
                label=cached.label,
                source=cached.source,
                confidence=cached.confidence,
                is_valid_bound=cached.is_valid_bound,
                needs_review=cached.needs_review,
                cache_hit=True,
            )

        # 2. Check persistent DB GeocodeCache
        stmt = select(GeocodeCache).where(GeocodeCache.key == cache_key)
        db_res = (await db.execute(stmt)).scalar_one_or_none()
        if db_res:
            res = GeocodeResult(
                lat=db_res.lat,
                lng=db_res.lng,
                label=db_res.label,
                source=db_res.source,
                confidence=1.0 if db_res.source == "google" else 0.7,
                is_valid_bound=True,
                needs_review=False,
                cache_hit=True,
            )
            MEMORY_GEOCODE_CACHE[cache_key] = res
            return res

        # 3. Call Google Geocoding API
        resolved_result: Optional[GeocodeResult] = None
        if self.google_api_key:
            try:
                resolved_result = await self._call_google(google_params, display_query)
            except Exception as e:
                logger.warning(f"Google geocoding error for {display_query}: {e}")

        # 4. Fallback to Nominatim if Google failed or returned no results
        if not resolved_result:
            try:
                resolved_result = await self._call_nominatim(nominatim_queries, display_query)
            except Exception as e:
                logger.warning(f"Nominatim geocoding error for {display_query}: {e}")

        if not resolved_result:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "GEOCODE_ERROR",
                    "message": f"Could not resolve geographic coordinates for {display_query}.",
                },
            )

        # 5. Persist to DB and in-memory cache
        new_cache_entry = GeocodeCache(
            key=cache_key,
            lat=resolved_result.lat,
            lng=resolved_result.lng,
            label=resolved_result.label,
            source=resolved_result.source,
        )
        db.add(new_cache_entry)
        await db.commit()
        MEMORY_GEOCODE_CACHE[cache_key] = resolved_result

        return resolved_result

    async def _call_google(
        self, params: Dict[str, Any], query_label: str
    ) -> Optional[GeocodeResult]:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return None
            data = resp.json()
            if data.get("status") != "OK" or not data.get("results"):
                return None

            result = data["results"][0]
            loc = result["geometry"]["location"]
            lat = float(loc["lat"])
            lng = float(loc["lng"])
            formatted = result.get("formatted_address", query_label)

            return GeocodeResult(
                lat=lat,
                lng=lng,
                label=formatted,
                source="google",
                confidence=1.0,
                is_valid_bound=True,
                needs_review=False,
                cache_hit=False,
            )

    async def _call_nominatim(
        self, queries: list[str], fallback_label: str
    ) -> Optional[GeocodeResult]:
        global _last_nominatim_time
        elapsed = time.time() - _last_nominatim_time
        if elapsed < 1.05:
            await asyncio.sleep(1.05 - elapsed)
        _last_nominatim_time = time.time()

        url = "https://nominatim.openstreetmap.org/search"
        headers = {
            "User-Agent": "MandiArbitrageAdvisor/0.01.00 (mandi-arbitrage@advisor.local)",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(headers=headers, timeout=3.0) as client:
            for q in queries:
                try:
                    resp = await client.get(url, params={"q": q, "format": "json", "limit": 1})
                    if resp.status_code == 200:
                        data = resp.json()
                        if data:
                            item = data[0]
                            lat = float(item["lat"])
                            lng = float(item["lon"])
                            display_name = item.get("display_name", fallback_label)
                            return GeocodeResult(
                                lat=lat,
                                lng=lng,
                                label=display_name,
                                source="nominatim",
                                confidence=0.7,
                                is_valid_bound=True,
                                needs_review=False,
                                cache_hit=False,
                            )
                except Exception as e:
                    logger.warning(f"Nominatim lookup failed for query '{q}': {e}")
                    await asyncio.sleep(0.5)

        return None
