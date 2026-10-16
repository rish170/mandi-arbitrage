import asyncio
from decimal import Decimal
import pytest
import respx
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db import Base
from app.models import DistanceCache, GeocodeCache
from app.services.geocode import GeocodingService, MEMORY_GEOCODE_CACHE
from app.services.distance import DistanceService, MEMORY_DISTANCE_CACHE

@pytest.fixture
async def in_memory_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()

@pytest.mark.asyncio
async def test_geocode_google_success(in_memory_db):
    """Google Geocoding succeeds on pincode query."""
    MEMORY_GEOCODE_CACHE.clear()
    geocoder = GeocodingService(google_api_key="TEST_KEY")

    with respx.mock(base_url="https://maps.googleapis.com") as respx_mock:
        respx_mock.get("/maps/api/geocode/json").respond(
            200,
            json={
                "status": "OK",
                "results": [
                    {
                        "geometry": {"location": {"lat": 21.1458, "lng": 79.0882}},
                        "formatted_address": "Nagpur, Maharashtra 440001, India",
                    }
                ],
            },
        )
        res = await geocoder.resolve_location(in_memory_db, pincode="440001")
        assert res.lat == 21.1458
        assert res.lng == 79.0882
        assert res.source == "google"
        assert res.cache_hit is False

        # Subsequent call should hit in-memory cache
        res2 = await geocoder.resolve_location(in_memory_db, pincode="440001")
        assert res2.cache_hit is True
        assert res2.source == "google"

@pytest.mark.asyncio
async def test_geocode_fallback_to_nominatim(in_memory_db):
    """When Google Geocoding returns 403 or DENIED, fallback to Nominatim."""
    MEMORY_GEOCODE_CACHE.clear()
    geocoder = GeocodingService(google_api_key="BAD_KEY")

    with respx.mock(assert_all_called=False) as respx_mock:
        # Google fails
        respx_mock.get("https://maps.googleapis.com/maps/api/geocode/json").respond(
            200, json={"status": "REQUEST_DENIED", "results": []}
        )
        # Nominatim succeeds
        respx_mock.get("https://nominatim.openstreetmap.org/search").respond(
            200,
            json=[
                {
                    "lat": "21.146",
                    "lon": "79.089",
                    "display_name": "Nagpur, Maharashtra, India",
                }
            ],
        )

        res = await geocoder.resolve_location(in_memory_db, pincode="440002")
        assert round(res.lat, 2) == 21.15
        assert round(res.lng, 2) == 79.09
        assert res.source == "nominatim"

@pytest.mark.asyncio
async def test_distance_routes_api_success(in_memory_db):
    """Google Routes API computeRouteMatrix succeeds and parses streamed array."""
    MEMORY_DISTANCE_CACHE.clear()
    dist_service = DistanceService(google_api_key="TEST_KEY", timeout=1.2)

    with respx.mock(base_url="https://routes.googleapis.com") as respx_mock:
        respx_mock.post("/distanceMatrix/v2:computeRouteMatrix").respond(
            200,
            json=[
                {
                    "originIndex": 0,
                    "destinationIndex": 0,
                    "status": {},
                    "condition": "ROUTE_EXISTS",
                    "distanceMeters": 25400,
                    "duration": "1800s",
                }
            ],
        )

        destinations = [(101, 21.15, 79.10)]
        results, has_fallback = await dist_service.get_distances(
            db=in_memory_db,
            origin_lat=21.1458,
            origin_lng=79.0882,
            origin_key="440001",
            destinations=destinations,
        )

        assert 101 in results
        assert results[101].road_km == 25.40
        assert results[101].duration_min == 30.0
        assert results[101].source == "routes_api"
        assert has_fallback is False

@pytest.mark.asyncio
async def test_distance_routes_api_timeout_fallback(in_memory_db):
    """When Google Routes API times out, fallback to haversine * 1.3 without raising error."""
    MEMORY_DISTANCE_CACHE.clear()
    dist_service = DistanceService(google_api_key="TEST_KEY", timeout=0.1)

    with respx.mock(base_url="https://routes.googleapis.com") as respx_mock:
        respx_mock.post("/distanceMatrix/v2:computeRouteMatrix").mock(
            side_effect=httpx.TimeoutException("Route matrix timed out after 1.2s")
        )

        destinations = [(202, 21.30, 79.25)]
        results, has_fallback = await dist_service.get_distances(
            db=in_memory_db,
            origin_lat=21.1458,
            origin_lng=79.0882,
            origin_key="timeout_test",
            destinations=destinations,
        )

        assert 202 in results
        assert results[202].source == "haversine_fallback"
        assert results[202].road_km > 0.0
        assert results[202].duration_min > 0.0
        assert has_fallback is True

@pytest.mark.asyncio
async def test_distance_routes_api_429_quota_fallback(in_memory_db):
    """When Google Routes API returns 429 quota exceeded, fallback gracefully."""
    MEMORY_DISTANCE_CACHE.clear()
    dist_service = DistanceService(google_api_key="TEST_KEY", timeout=1.2)

    with respx.mock(base_url="https://routes.googleapis.com") as respx_mock:
        respx_mock.post("/distanceMatrix/v2:computeRouteMatrix").respond(
            429,
            json={"error": {"code": 429, "message": "Resource has been exhausted (e.g. check quota)."}},
        )

        destinations = [(303, 21.50, 79.50)]
        results, has_fallback = await dist_service.get_distances(
            db=in_memory_db,
            origin_lat=21.1458,
            origin_lng=79.0882,
            origin_key="quota_test",
            destinations=destinations,
        )

        assert 303 in results
        assert results[303].source == "haversine_fallback"
        assert has_fallback is True

@pytest.mark.asyncio
async def test_distance_per_element_failure(in_memory_db):
    """When one element has ROUTE_NOT_FOUND, fallback for that element only."""
    MEMORY_DISTANCE_CACHE.clear()
    dist_service = DistanceService(google_api_key="TEST_KEY", timeout=1.2)

    with respx.mock(base_url="https://routes.googleapis.com") as respx_mock:
        respx_mock.post("/distanceMatrix/v2:computeRouteMatrix").respond(
            200,
            json=[
                {
                    "originIndex": 0,
                    "destinationIndex": 0,
                    "status": {},
                    "condition": "ROUTE_EXISTS",
                    "distanceMeters": 15000,
                    "duration": "1200s",
                },
                {
                    "originIndex": 0,
                    "destinationIndex": 1,
                    "status": {"code": 5, "message": "No route found"},
                    "condition": "ROUTE_NOT_FOUND",
                },
            ],
        )

        destinations = [(401, 21.20, 79.15), (402, 21.90, 80.00)]
        results, has_fallback = await dist_service.get_distances(
            db=in_memory_db,
            origin_lat=21.1458,
            origin_lng=79.0882,
            origin_key="element_fail_test",
            destinations=destinations,
        )

        assert results[401].source == "routes_api"
        assert results[401].road_km == 15.0
        assert results[402].source == "haversine_fallback"
        assert has_fallback is True
