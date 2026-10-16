import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.01.00"
        assert "timestamp" in data
        assert "X-Process-Time-ms" in response.headers

@pytest.mark.asyncio
async def test_root_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_meta_rates():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/meta/rates")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ASSUMPTION_UNVERIFIED"
        assert "vehicles" in data
        assert "market_fee_pct_default" in data
        assert float(data["market_fee_pct_default"]) == 1.0

@pytest.mark.asyncio
async def test_meta_crops():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/meta/crops")
        assert response.status_code == 200
        data = response.json()
        assert "crops" in data
        assert len(data["crops"]) == 7

@pytest.mark.asyncio
async def test_meta_vehicles():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/meta/vehicles")
        assert response.status_code == 200
        data = response.json()
        assert "vehicles" in data
        assert "tempo" in data["vehicles"]
        assert "pickup" in data["vehicles"]

@pytest.mark.asyncio
async def test_unimplemented_routes_return_501():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test compare
        res_compare = await client.post(
            "/api/v1/compare",
            json={
                "pincode": "411001",
                "commodity": "Wheat",
                "quantity_quintals": 10,
                "vehicle": "pickup",
                "quality": {"grade": "Good"},
                "price_basis": "modal",
                "include_other_charges": False,
                "limit": 5,
            },
        )
        assert res_compare.status_code == 501
        assert res_compare.json()["error"]["code"] == "NOT_IMPLEMENTED"

        # Test trend
        res_trend = await client.get(
            "/api/v1/trend?mandi_ids=1,2&commodity=Wheat"
        )
        assert res_trend.status_code == 501
        assert res_trend.json()["error"]["code"] == "NOT_IMPLEMENTED"

@pytest.mark.asyncio
async def test_validation_error_format():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Invalid pincode: "012345" starts with 0
        res = await client.post(
            "/api/v1/compare",
            json={
                "pincode": "012345",
                "commodity": "Wheat",
            },
        )
        assert res.status_code == 422
        body = res.json()
        assert "error" in body
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert "details" in body["error"]
