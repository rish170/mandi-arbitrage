"""End-to-End integration test script for Mandi Arbitrage Advisor.
Tests health, metadata, 3 compare pincodes, trend, and schema conformance.
"""
import sys
import time
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_integration():
    print(f"Connecting to backend at {BASE_URL}...")
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 1. Health check
    print("Testing /health...")
    resp = client.get("/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    health_data = resp.json()
    assert health_data.get("status") == "ok", f"Unexpected health status: {health_data}"
    print("  PASS: /health returned status ok")

    # 2. Meta endpoints
    print("Testing metadata endpoints...")
    # Crops
    resp = client.get("/meta/crops")
    assert resp.status_code == 200, f"/meta/crops failed: {resp.text}"
    crops = resp.json()
    assert "crops" in crops and len(crops["crops"]) > 0
    crop_ids = [c["id"] for c in crops["crops"]]
    print(f"  PASS: /meta/crops returned {len(crops['crops'])} crops ({crop_ids[:3]}...)")

    # Vehicles
    resp = client.get("/meta/vehicles")
    assert resp.status_code == 200, f"/meta/vehicles failed: {resp.text}"
    vehicles = resp.json().get("vehicles", {})
    assert "tempo" in vehicles and "truck" in vehicles
    print(f"  PASS: /meta/vehicles returned {list(vehicles.keys())}")

    # Districts
    resp = client.get("/meta/districts?state=Maharashtra")
    assert resp.status_code == 200, f"/meta/districts failed: {resp.text}"
    districts = resp.json().get("districts", [])
    assert len(districts) > 0
    print(f"  PASS: /meta/districts returned {len(districts)} districts")

    # Rates
    resp = client.get("/meta/rates")
    assert resp.status_code == 200, f"/meta/rates failed: {resp.text}"
    rates = resp.json()
    assert "market_fee_pct_default" in rates and "status" in rates
    print(f"  PASS: /meta/rates returned rates with status={rates.get('status')}")

    # 3. Compare for 3 distinct pincodes
    scenarios = [
        {
            "name": "Nagpur Wheat (440001)",
            "payload": {
                "pincode": "440001",
                "commodity": "Wheat",
                "quantity_quintals": 10.0,
                "vehicle": "tempo",
                "quality": {"grade": "Good"},
                "price_basis": "modal",
                "include_other_charges": False,
                "limit": 5,
            },
        },
        {
            "name": "Pune Onion (411001)",
            "payload": {
                "pincode": "411001",
                "commodity": "Onion",
                "quantity_quintals": 25.0,
                "vehicle": "pickup",
                "quality": {"grade": "Average"},
                "price_basis": "modal",
                "include_other_charges": True,
                "limit": 5,
            },
        },
        {
            "name": "Nashik Tomato (422001)",
            "payload": {
                "pincode": "422001",
                "commodity": "Tomato",
                "quantity_quintals": 15.0,
                "vehicle": "mini_truck",
                "quality": {"grade": "Below average"},
                "price_basis": "modal",
                "include_other_charges": False,
                "limit": 5,
            },
        },
    ]

    all_mandi_ids = set()

    for sc in scenarios:
        print(f"Testing /compare for {sc['name']}...")
        start_t = time.perf_counter()
        resp = client.post("/compare", json=sc["payload"])
        elapsed = (time.perf_counter() - start_t) * 1000
        assert resp.status_code == 200, f"Compare failed for {sc['name']}: {resp.status_code} {resp.text}"
        data = resp.json()

        # Contract checks
        assert "query" in data, "Missing query in response"
        assert "results" in data, "Missing results in response"
        assert "summary" in data, "Missing summary in response"
        assert "assumptions" in data, "Missing assumptions in response"
        assert "warnings" in data, "Missing warnings in response"
        assert "meta" in data, "Missing meta in response"

        results = data["results"]
        assert len(results) > 0, f"No mandis found for {sc['name']}"

        for r in results:
            all_mandi_ids.add(r["mandi"]["id"])
            assert "rank" in r
            assert "is_nearest" in r
            assert "mandi" in r and "name" in r["mandi"]
            assert "price" in r and "value" in r["price"]
            assert "distance" in r and "road_km" in r["distance"]
            assert "breakdown" in r
            bd = r["breakdown"]
            for field in ["price_q", "quality_cut_q", "realized_q", "mandi_fee_q", "transport_q", "other_q", "net_q", "net_total"]:
                assert field in bd, f"Missing {field} in breakdown"
            assert "vs_nearest" in r and "delta_q" in r["vs_nearest"]

        summary = data["summary"]
        assert "best_mandi_id" in summary
        assert "nearest_mandi_id" in summary
        assert "extra_profit_q" in summary

        print(f"  PASS: {sc['name']} returned {len(results)} mandis in {elapsed:.1f}ms")
        print(f"        Best: Mandi #{summary['best_mandi_id']}, Nearest: Mandi #{summary['nearest_mandi_id']}, Extra/q: Rs {summary['extra_profit_q']}")

    # 4. Trend endpoint
    mandi_id_list = list(all_mandi_ids)[:5]
    print(f"Testing /trend for mandi IDs {mandi_id_list} (Wheat)...")
    resp = client.get("/trend", params={"mandi_ids": ",".join(str(m) for m in mandi_id_list), "commodity": "Wheat", "days": 7})
    assert resp.status_code == 200, f"/trend failed: {resp.status_code} {resp.text}"
    trend_data = resp.json()
    assert "series" in trend_data
    series = trend_data["series"]
    assert len(series) > 0
    for s in series:
        assert "mandi_id" in s
        assert "mandi_name" in s
        assert "points" in s
        for pt in s["points"]:
            assert "date" in pt
            assert "is_seeded" in pt
    print(f"  PASS: /trend returned {len(series)} series with {len(series[0]['points'])} points each")

    print("\nALL INTEGRATION CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        test_integration()
    except Exception as e:
        print(f"\nINTEGRATION TEST FAILED: {e}", file=sys.stderr)
        sys.exit(1)
