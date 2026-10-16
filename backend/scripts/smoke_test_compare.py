import json
import subprocess
import sys
import time
import httpx
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
VENV_PYTHON = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"

def run_smoke_test():
    print("Starting uvicorn server for smoke test...")
    cmd = [
        str(VENV_PYTHON),
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--app-dir",
        str(BACKEND_DIR),
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(BACKEND_DIR))
    
    try:
        # Wait up to 10 seconds for server to start
        base_url = "http://127.0.0.1:8000"
        started = False
        for _ in range(20):
            try:
                r = httpx.get(f"{base_url}/health", timeout=1.0)
                if r.status_code == 200:
                    started = True
                    break
            except Exception:
                time.sleep(0.5)

        if not started:
            print("Failed to start server within timeout.")
            return

        payload = {
            "pincode": "440001",
            "commodity": "Wheat",
            "quantity_quintals": 10,
            "vehicle": "pickup",
            "quality": {"grade": "Good"},
            "price_basis": "modal",
            "include_other_charges": False,
            "limit": 5,
        }

        # 1. Cold Call
        print("\n--- COLD CALL ---")
        t0 = time.perf_counter()
        r_cold = httpx.post(f"{base_url}/api/v1/compare", json=payload, timeout=10.0)
        t_cold_client = (time.perf_counter() - t0) * 1000.0
        assert r_cold.status_code == 200, f"Cold call failed: {r_cold.text}"
        data_cold = r_cold.json()

        print(f"Status Code: {r_cold.status_code}")
        print(f"Server meta.elapsed_ms: {data_cold['meta']['elapsed_ms']} ms")
        print(f"Client total time: {t_cold_client:.2f} ms")
        print(f"Cache status: {data_cold['meta']['cache']}")
        print(f"Warnings: {[w['code'] for w in data_cold['warnings']]}")

        # 2. Warm Call
        print("\n--- WARM CALL ---")
        t0 = time.perf_counter()
        r_warm = httpx.post(f"{base_url}/api/v1/compare", json=payload, timeout=10.0)
        t_warm_client = (time.perf_counter() - t0) * 1000.0
        assert r_warm.status_code == 200, f"Warm call failed: {r_warm.text}"
        data_warm = r_warm.json()

        print(f"Status Code: {r_warm.status_code}")
        print(f"Server meta.elapsed_ms: {data_warm['meta']['elapsed_ms']} ms")
        print(f"Client total time: {t_warm_client:.2f} ms")
        print(f"Cache status: {data_warm['meta']['cache']}")

        # 3. Print first 2 results trimmed
        print("\n--- FIRST TWO RESULTS (TRIMMED) ---")
        for i, res in enumerate(data_cold["results"][:2], 1):
            trimmed = {
                "rank": res["rank"],
                "is_nearest": res["is_nearest"],
                "mandi": {
                    "id": res["mandi"]["id"],
                    "name": res["mandi"]["name"],
                    "district": res["mandi"]["district"],
                },
                "price": {
                    "basis": res["price"]["basis"],
                    "value": res["price"]["value"],
                    "variety": res["price"]["variety"],
                    "is_stale": res["price"]["is_stale"],
                },
                "distance": res["distance"],
                "breakdown": {
                    "price_q": res["breakdown"]["price_q"],
                    "transport_q": res["breakdown"]["transport_q"],
                    "mandi_fee_q": res["breakdown"]["mandi_fee_q"],
                    "net_q": res["breakdown"]["net_q"],
                    "net_total": res["breakdown"]["net_total"],
                },
                "vs_nearest": res["vs_nearest"],
            }
            print(f"Result #{i}:")
            print(json.dumps(trimmed, indent=2))

        print("\n--- SUMMARY ---")
        print(json.dumps(data_cold["summary"], indent=2))

    finally:
        print("\nStopping uvicorn server...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("Server stopped cleanly.")

if __name__ == "__main__":
    run_smoke_test()
