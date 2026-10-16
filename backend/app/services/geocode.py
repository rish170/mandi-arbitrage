import asyncio
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, Optional
import httpx
from pydantic import BaseModel
from app.config import settings

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

class GeocodingService:
    def __init__(self, google_api_key: Optional[str] = None):
        self.google_api_key = google_api_key or settings.GOOGLE_MAPS_API_KEY
        self._last_nominatim_time = 0.0
        self._cache: Dict[str, GeocodeResult] = {}

    async def geocode(
        self, query: str, state: str, district: Optional[str] = None
    ) -> Optional[GeocodeResult]:
        cache_key = f"{state}:{district or ''}:{query}".lower().strip()
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 1. Attempt Google Geocoding if API key is present
        if self.google_api_key:
            try:
                res = await self._geocode_google(query, state)
                if res:
                    self._cache[cache_key] = res
                    return res
            except Exception as e:
                logger.warning(f"Google geocoding error for '{query}': {e}. Falling back to Nominatim.")

        # 2. Fallback to Nominatim
        res = await self._geocode_nominatim(query, state, district)
        if res:
            self._cache[cache_key] = res
            return res

        return None

    async def _geocode_google(self, query: str, state: str) -> Optional[GeocodeResult]:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": query,
            "key": self.google_api_key,
        }
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                logger.warning(f"Google geocode HTTP {resp.status_code}")
                return None
            data = resp.json()
            status = data.get("status")
            if status != "OK" or not data.get("results"):
                logger.warning(f"Google geocode status {status} for {query}")
                return None

            result = data["results"][0]
            loc = result["geometry"]["location"]
            lat = float(loc["lat"])
            lng = float(loc["lng"])
            location_type = result["geometry"].get("location_type", "APPROXIMATE")

            confidence_map = {
                "ROOFTOP": 1.0,
                "RANGE_INTERPOLATED": 0.85,
                "GEOMETRIC_CENTER": 0.70,
                "APPROXIMATE": 0.50,
            }
            confidence = confidence_map.get(location_type, 0.50)
            in_bound = is_within_state_bounds(lat, lng, state)
            needs_review = (not in_bound) or (confidence < 0.6)

            return GeocodeResult(
                lat=lat,
                lng=lng,
                label=result.get("formatted_address", query),
                source="google",
                confidence=confidence if in_bound else 0.1,
                is_valid_bound=in_bound,
                needs_review=needs_review,
            )

    async def _geocode_nominatim(
        self, query: str, state: str, district: Optional[str] = None
    ) -> Optional[GeocodeResult]:
        # Respect 1 req/sec rate limit for Nominatim
        elapsed = time.time() - self._last_nominatim_time
        if elapsed < 1.05:
            await asyncio.sleep(1.05 - elapsed)
        self._last_nominatim_time = time.time()

        url = "https://nominatim.openstreetmap.org/search"
        headers = {
            "User-Agent": "MandiArbitrageAdvisor/0.01.00 (mandi-arbitrage@advisor.local)",
            "Accept": "application/json",
        }

        # Try specific query first, then fallback to district/city if needed
        queries_to_try = [query]
        if district:
            queries_to_try.append(f"{district}, {state}, India")

        async with httpx.AsyncClient(headers=headers, timeout=5.0) as client:
            for q in queries_to_try:
                try:
                    params = {"q": q, "format": "json", "limit": 1}
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        results = resp.json()
                        if results:
                            item = results[0]
                            lat = float(item["lat"])
                            lng = float(item["lon"])
                            importance = float(item.get("importance", 0.50))
                            in_bound = is_within_state_bounds(lat, lng, state)
                            # Slightly lower confidence if fallback query had to be used
                            is_fallback = q != query
                            confidence = min(0.75, importance) if not is_fallback else 0.50
                            needs_review = (not in_bound) or is_fallback or (confidence < 0.6)

                            return GeocodeResult(
                                lat=lat,
                                lng=lng,
                                label=item.get("display_name", q),
                                source="nominatim",
                                confidence=confidence if in_bound else 0.1,
                                is_valid_bound=in_bound,
                                needs_review=needs_review,
                            )
                except Exception as e:
                    logger.warning(f"Nominatim lookup failed for '{q}': {e}")
                    await asyncio.sleep(1.0)

        return None
