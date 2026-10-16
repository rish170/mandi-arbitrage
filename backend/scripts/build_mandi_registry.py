import argparse
import asyncio
import csv
import json
import logging
from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.services.datagov import DataGovClient
from app.services.geocode import GeocodingService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = backend_dir.parent
BACKEND_DATA_DIR = backend_dir / "data"
ROOT_DATA_DIR = ROOT_DIR / "data"

for d in (BACKEND_DATA_DIR, ROOT_DATA_DIR):
    d.mkdir(parents=True, exist_ok=True)

SEED_FILE_BACKEND = BACKEND_DATA_DIR / "mandis.seed.json"
SEED_FILE_ROOT = ROOT_DATA_DIR / "mandis.seed.json"
REVIEW_FILE_BACKEND = BACKEND_DATA_DIR / "mandis_review.csv"
REVIEW_FILE_ROOT = ROOT_DATA_DIR / "mandis_review.csv"
CACHE_FILE = BACKEND_DATA_DIR / "geocode_cache.json"

def clean_market_name(name: str) -> str:
    cleaned = name.strip()
    return cleaned

async def fetch_distinct_markets(states: list[str]) -> list[dict]:
    client = DataGovClient()
    all_markets: dict[str, dict] = {}

    for state in states:
        logger.info(f"Fetching market records from data.gov.in for state: {state}...")
        records = await client.fetch_records(state=state, page_size=500)
        logger.info(f"Retrieved {len(records)} records for {state}")
        for r in records:
            market_clean = clean_market_name(r.market)
            key = f"{r.state}:{r.district}:{market_clean}".lower()
            if key not in all_markets:
                all_markets[key] = {
                    "state": r.state,
                    "district": r.district,
                    "name": market_clean,
                }

    logger.info(f"Found {len(all_markets)} unique markets across specified states.")
    return list(all_markets.values())

def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

async def build_registry(states: list[str], max_markets: int | None = None):
    markets = await fetch_distinct_markets(states)
    if max_markets:
        markets = markets[:max_markets]

    geocoder = GeocodingService()
    cache = load_cache()

    registry = []
    review_list = []

    total = len(markets)
    logger.info(f"Starting geocoding process for {total} mandis...")

    for idx, m in enumerate(markets, 1):
        state = m["state"]
        district = m["district"]
        name = m["name"]
        cache_key = f"{state}:{district}:{name}".lower()

        if cache_key in cache:
            cached_data = cache[cache_key]
            entry = {
                "id": idx,
                "state": state,
                "district": district,
                "name": name,
                "lat": cached_data["lat"],
                "lng": cached_data["lng"],
                "geocode_source": cached_data["geocode_source"],
                "geocode_confidence": cached_data["geocode_confidence"],
                "needs_review": cached_data["needs_review"],
            }
        else:
            query = f"{name} APMC, {district}, {state}, India"
            res = await geocoder.geocode(query, state, district)
            if res:
                entry = {
                    "id": idx,
                    "state": state,
                    "district": district,
                    "name": name,
                    "lat": res.lat,
                    "lng": res.lng,
                    "geocode_source": res.source,
                    "geocode_confidence": res.confidence,
                    "needs_review": res.needs_review,
                }
                cache[cache_key] = {
                    "lat": res.lat,
                    "lng": res.lng,
                    "geocode_source": res.source,
                    "geocode_confidence": res.confidence,
                    "needs_review": res.needs_review,
                }
            else:
                # Completely failed geocode
                entry = {
                    "id": idx,
                    "state": state,
                    "district": district,
                    "name": name,
                    "lat": 0.0,
                    "lng": 0.0,
                    "geocode_source": "failed",
                    "geocode_confidence": 0.0,
                    "needs_review": True,
                }
                cache[cache_key] = {
                    "lat": 0.0,
                    "lng": 0.0,
                    "geocode_source": "failed",
                    "geocode_confidence": 0.0,
                    "needs_review": True,
                }

            save_cache(cache)

        registry.append(entry)
        if entry["needs_review"]:
            review_list.append(entry)

        if idx % 10 == 0 or idx == total:
            logger.info(f"Processed {idx}/{total} mandis (Needs review: {len(review_list)})")

    # Save to seed files
    for seed_file in (SEED_FILE_BACKEND, SEED_FILE_ROOT):
        with open(seed_file, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved registry to {seed_file}")

    # Write review CSV
    for review_file in (REVIEW_FILE_BACKEND, REVIEW_FILE_ROOT):
        with open(review_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "state",
                    "district",
                    "name",
                    "lat",
                    "lng",
                    "geocode_source",
                    "geocode_confidence",
                    "needs_review",
                ],
            )
            writer.writeheader()
            for r in review_list:
                writer.writerow(r)
        logger.info(f"Saved review list to {review_file}")

    geocoded_ok = total - len(review_list)
    print("\n" + "=" * 50)
    print("MANDI REGISTRY BUILD SUMMARY")
    print("=" * 50)
    print(f"Total Mandis Processed : {total}")
    print(f"Geocoded Confidently   : {geocoded_ok}")
    print(f"Needs Manual Review    : {len(review_list)}")
    print(f"Review CSV Output      : {REVIEW_FILE_ROOT}")
    print(f"Seed Output            : {SEED_FILE_ROOT}")
    print("=" * 50 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Build Mandi Registry from data.gov.in")
    parser.add_argument(
        "--states",
        nargs="+",
        default=["Maharashtra"],
        help="List of states to build registry for (default: Maharashtra)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of markets to geocode (for quick tests)",
    )
    args = parser.parse_args()
    asyncio.run(build_registry(args.states, args.limit))

if __name__ == "__main__":
    main()
