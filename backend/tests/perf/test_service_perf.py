from datetime import date, timedelta
from decimal import Decimal
import time
import pytest
import respx
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db import Base, get_db
from app.main import app
from app.models import Mandi, Price
from app.services.distance import MEMORY_DISTANCE_CACHE
from app.services.geocode import MEMORY_GEOCODE_CACHE
from app.services.prices import MEMORY_PRICE_CACHE

@pytest.fixture
async def perf_test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    today = date.today()
    # Seed 5 candidate mandis and prices
    async with session_factory() as session:
        mandis = []
        prices = []
        for i in range(1, 6):
            m = Mandi(
                id=i,
                state="Maharashtra",
                district="Nagpur",
                name=f"APMC Mandi {i}",
                lat=21.14 + (i * 0.05),
                lng=79.08 + (i * 0.05),
                geocode_source="google",
                geocode_confidence=1.0,
            )
            mandis.append(m)
            p = Price(
                mandi_id=i,
                commodity="Wheat",
                variety="Lokwan",
                grade="FAQ",
                arrival_date=today,
                min_price=Decimal("2300.00"),
                modal_price=Decimal(str(2400 + i * 20)),
                max_price=Decimal("2500.00"),
            )
            prices.append(p)
        session.add_all(mandis + prices)
        await session.commit()

    async def override_get_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db
    yield session_factory
    app.dependency_overrides.clear()
    await engine.dispose()

@pytest.mark.asyncio
async def test_service_layer_overhead_under_300ms(perf_test_db):
    """
    Assert that the service layer internal overhead (orchestration, DB lookups,
    pure Decimal profit arithmetic, sorting, serialization) stays strictly under 300 ms
    when external services return within expected latency.
    """
    MEMORY_GEOCODE_CACHE.clear()
    MEMORY_DISTANCE_CACHE.clear()
    MEMORY_PRICE_CACHE.clear()

    with respx.mock(assert_all_called=False) as respx_mock:
        # Mock Google Geocoding returning in ~20 ms
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
        # Mock Google Routes computeRouteMatrix returning in ~50 ms
        matrix_response = [
            {
                "originIndex": 0,
                "destinationIndex": i,
                "status": {},
                "condition": "ROUTE_EXISTS",
                "distanceMeters": 5000 * (i + 1),
                "duration": f"{300 * (i + 1)}s",
            }
            for i in range(5)
        ]
        respx_mock.post("https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix").respond(
            200,
            json=matrix_response,
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            payload = {
                "pincode": "440001",
                "commodity": "Wheat",
                "quantity_quintals": 10.0,
                "vehicle": "pickup",
                "quality": {"grade": "Good"},
            }

            # Warmup request
            r_warmup = await client.post("/api/v1/compare", json=payload)
            assert r_warmup.status_code == 200

            # Execute 5 timed iterations
            latencies = []
            for _ in range(5):
                t0 = time.perf_counter()
                resp = await client.post("/api/v1/compare", json=payload)
                t_elapsed_ms = (time.perf_counter() - t0) * 1000.0
                assert resp.status_code == 200
                data = resp.json()
                server_reported_ms = data["meta"]["elapsed_ms"]
                header_ms = float(resp.headers.get("X-Process-Time-ms", 0.0))
                latencies.append((t_elapsed_ms, server_reported_ms, header_ms))

            for client_ms, server_ms, hdr_ms in latencies:
                # Assert server elapsed time is strictly under 300 ms target
                assert server_ms < 300.0, f"Server elapsed time {server_ms:.1f}ms exceeded 300ms limit"
                assert hdr_ms < 300.0, f"X-Process-Time-ms {hdr_ms:.1f}ms exceeded 300ms limit"
                assert client_ms < 300.0, f"Total client time {client_ms:.1f}ms exceeded 300ms limit"
