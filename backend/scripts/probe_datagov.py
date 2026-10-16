import asyncio
from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import httpx
from app.config import settings

async def fetch_with_retry(client, url, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(2 * (attempt + 1))
    return None

async def main():
    headers = {
        "User-Agent": "MandiArbitrageAdvisor/0.01.00",
        "Accept": "application/json",
    }
    timeout = httpx.Timeout(30.0, connect=15.0)
    url = f"https://api.data.gov.in/resource/{settings.DATAGOV_RESOURCE_ID}"

    async with httpx.AsyncClient(headers=headers, timeout=timeout) as client:
        # Test 1: Query with filters[arrival_date]=15/10/2026
        params = {
            "api-key": settings.DATA_GOV_API_KEY,
            "format": "json",
            "limit": 5,
            "filters[state.keyword]": "Maharashtra",
            "filters[arrival_date]": "15/10/2026",
        }
        print("Testing filters[arrival_date]=15/10/2026...")
        data = await fetch_with_retry(client, url, params)
        if data:
            records = data.get("records", [])
            print(f"Total: {data.get('total')}, Count: {data.get('count')}")
            for r in records:
                print(f"  Record arrival_date: {r.get('arrival_date')}, Market: {r.get('market')}, Commodity: {r.get('commodity')}")

        # Test 2: Query with filters[arrival_date.keyword]=15/10/2026
        params2 = {
            "api-key": settings.DATA_GOV_API_KEY,
            "format": "json",
            "limit": 5,
            "filters[state.keyword]": "Maharashtra",
            "filters[arrival_date.keyword]": "15/10/2026",
        }
        print("\nTesting filters[arrival_date.keyword]=15/10/2026...")
        data2 = await fetch_with_retry(client, url, params2)
        if data2:
            records2 = data2.get("records", [])
            print(f"Total: {data2.get('total')}, Count: {data2.get('count')}")
            for r in records2:
                print(f"  Record arrival_date: {r.get('arrival_date')}, Market: {r.get('market')}, Commodity: {r.get('commodity')}")

        # Test 3: Query with an impossible date: 01/01/2000
        params3 = {
            "api-key": settings.DATA_GOV_API_KEY,
            "format": "json",
            "limit": 5,
            "filters[state.keyword]": "Maharashtra",
            "filters[arrival_date]": "01/01/2000",
        }
        print("\nTesting filters[arrival_date]=01/01/2000 (impossible date)...")
        data3 = await fetch_with_retry(client, url, params3)
        if data3:
            records3 = data3.get("records", [])
            print(f"Total: {data3.get('total')}, Count: {data3.get('count')}")
            for r in records3:
                print(f"  Record arrival_date: {r.get('arrival_date')}")

if __name__ == "__main__":
    asyncio.run(main())
