from datetime import date, timedelta
from decimal import Decimal
import pytest
import respx
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db import Base, get_db
from app.main import app
from app.models import Mandi, Price

@pytest.fixture
async def seeded_test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    today = date.today()
    # Seed 3 mandis and prices
    async with session_factory() as session:
        m1 = Mandi(
            id=1,
            state="Maharashtra",
            district="Nagpur",
            name="Nagpur APMC",
            lat=21.1458,
            lng=79.0882,
            geocode_source="google",
            geocode_confidence=1.0,
        )
        m2 = Mandi(
            id=2,
            state="Maharashtra",
            district="Nagpur",
            name="Katol APMC",
            lat=21.2750,
            lng=78.5870,
            geocode_source="google",
            geocode_confidence=1.0,
        )
        m3 = Mandi(
            id=3,
            state="Maharashtra",
            district="Wardha",
            name="Wardha APMC",
            lat=20.7453,
            lng=78.6022,
            geocode_source="google",
            geocode_confidence=1.0,
        )
        session.add_all([m1, m2, m3])

        # Add prices for Wheat
        p1 = Price(
            mandi_id=1,
            commodity="Wheat",
            variety="Lokwan",
            grade="FAQ",
            arrival_date=today,
            min_price=Decimal("2300.00"),
            modal_price=Decimal("2400.00"),
            max_price=Decimal("2500.00"),
        )
        p2 = Price(
            mandi_id=2,
            commodity="Wheat",
            variety="Lokwan",
            grade="FAQ",
            arrival_date=today,
            min_price=Decimal("2400.00"),
            modal_price=Decimal("2550.00"),
            max_price=Decimal("2650.00"),
        )
        p3 = Price(
            mandi_id=3,
            commodity="Wheat",
            variety="Sharbati",
            grade="FAQ",
            arrival_date=today - timedelta(days=2),  # Stale price (2 days old)
            min_price=Decimal("2500.00"),
            modal_price=Decimal("2700.00"),
            max_price=Decimal("2800.00"),
        )
        session.add_all([p1, p2, p3])
        await session.commit()

    async def override_get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db
    yield session_factory
    app.dependency_overrides.clear()
    await engine.dispose()

@pytest.mark.asyncio
async def test_compare_successful_flow_with_mocked_apis(seeded_test_db):
    """Full compare flow with mocked Google geocode and routes APIs."""
    with respx.mock(assert_all_called=False) as respx_mock:
        # Mock Google Geocoding
        respx_mock.get("https://maps.googleapis.com/maps/api/geocode/json").respond(
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
        # Mock Google Routes Matrix
        respx_mock.post("https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix").respond(
            200,
            json=[
                {
                    "originIndex": 0,
                    "destinationIndex": 0,
                    "status": {},
                    "condition": "ROUTE_EXISTS",
                    "distanceMeters": 5000,
                    "duration": "600s",
                },
                {
                    "originIndex": 0,
                    "destinationIndex": 1,
                    "status": {},
                    "condition": "ROUTE_EXISTS",
                    "distanceMeters": 60000,
                    "duration": "4500s",
                },
                {
                    "originIndex": 0,
                    "destinationIndex": 2,
                    "status": {},
                    "condition": "ROUTE_EXISTS",
                    "distanceMeters": 75000,
                    "duration": "5400s",
                },
            ],
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/compare",
                json={
                    "pincode": "440001",
                    "commodity": "Wheat",
                    "quantity_quintals": 10,
                    "vehicle": "pickup",
                    "quality": {"grade": "Good"},
                    "price_basis": "modal",
                    "include_other_charges": False,
                    "limit": 5,
                },
            )
            assert resp.status_code == 200
            data = resp.json()

            # Schema compliance
            assert "query" in data
            assert "results" in data
            assert "summary" in data
            assert "assumptions" in data
            assert "warnings" in data
            assert "meta" in data

            # Results verification
            assert len(data["results"]) == 3
            # Check ranks
            ranks = [r["rank"] for r in data["results"]]
            assert ranks == [1, 2, 3]

            # Check nearest flag
            nearest_items = [r for r in data["results"] if r["is_nearest"]]
            assert len(nearest_items) == 1
            assert nearest_items[0]["mandi"]["id"] == 1  # Nagpur APMC (5 km)

            # Check warnings: m3 price is 2 days old, so STALE_PRICE should trigger
            warning_codes = [w["code"] for w in data["warnings"]]
            assert "STALE_PRICE" in warning_codes
            assert "ASSUMED_RATES" in warning_codes

@pytest.mark.asyncio
async def test_compare_google_failure_returns_200_with_fallback(seeded_test_db):
    """When Google Routes API fails (e.g. 403), /compare still returns 200 with DISTANCE_FALLBACK warning."""
    from app.services.distance import MEMORY_DISTANCE_CACHE
    from app.services.geocode import MEMORY_GEOCODE_CACHE
    MEMORY_DISTANCE_CACHE.clear()
    MEMORY_GEOCODE_CACHE.clear()

    with respx.mock(assert_all_called=False) as respx_mock:
        # Mock Google Geocoding (success)
        respx_mock.get("https://maps.googleapis.com/maps/api/geocode/json").respond(
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
        # Mock Google Routes API failing with 403
        respx_mock.post("https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix").respond(
            403,
            json={"error": {"code": 403, "message": "Routes API disabled"}},
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/compare",
                json={
                    "pincode": "440099",
                    "commodity": "Wheat",
                    "quantity_quintals": 10,
                    "vehicle": "pickup",
                    "quality": {"grade": "Good"},
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            warning_codes = [w["code"] for w in data["warnings"]]
            assert "DISTANCE_FALLBACK" in warning_codes
            # Check source in results
            for r in data["results"]:
                assert r["distance"]["source"] == "haversine_fallback"

@pytest.mark.asyncio
async def test_error_shape_invalid_pincode():
    """Invalid pincode (starting with 0, not 6 digits) must return standard 422 error JSON."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Pincode starting with 0
        resp = await client.post(
            "/api/v1/compare",
            json={"pincode": "012345", "commodity": "Wheat"},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "VALIDATION_ERROR"

        # Pincode too short
        resp2 = await client.post(
            "/api/v1/compare",
            json={"pincode": "12345", "commodity": "Wheat"},
        )
        assert resp2.status_code == 422
        body2 = resp2.json()
        assert body2["error"]["code"] == "VALIDATION_ERROR"

@pytest.mark.asyncio
async def test_error_shape_unknown_crop():
    """Unsupported crop must return 422 with UNKNOWN_COMMODITY code."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/compare",
            json={"pincode": "440001", "commodity": "Dragonfruit"},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "UNKNOWN_COMMODITY"
        assert "Dragonfruit" in body["error"]["message"]

@pytest.mark.asyncio
async def test_error_shape_missing_location():
    """Missing both pincode and state/district must return 422 with MISSING_LOCATION."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/compare",
            json={"commodity": "Wheat"},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] == "MISSING_LOCATION"
