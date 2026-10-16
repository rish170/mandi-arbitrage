import argparse
import asyncio
import json
import logging
from pathlib import Path
import sys

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db import async_session_factory
from app.services.ingest import ingest_prices_for_crops

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

async def run_ingestion(states: list[str], crops: list[str] | None, backfill_days: int):
    if backfill_days > 0:
        logger.info(
            f"Note: --backfill-days {backfill_days} requested, but upstream data.gov.in resource "
            "only provides current daily snapshots (verified in Phase 2 probe). Running current snapshot ingest."
        )

    async with async_session_factory() as db:
        res = await ingest_prices_for_crops(db=db, states=states, crops=crops)
        data = res.to_dict()

        print("\n" + "=" * 50)
        print("PRICE INGESTION SUMMARY")
        print("=" * 50)
        print(f"Total Records Fetched : {data['records_fetched']}")
        print(f"Records Inserted      : {data['records_inserted']}")
        print(f"Records Updated       : {data['records_updated']}")
        print(f"Unmatched Markets     : {data['unmatched_count']}")
        print(f"Execution Duration    : {data['duration_seconds']}s")
        if data["unmatched_sample"]:
            print("\nSample Unmatched Records:")
            for u in data["unmatched_sample"][:5]:
                print(f"  - {u['market']} ({u['district']}, {u['state']}) -> {u['commodity']}")
        print("=" * 50 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Ingest daily mandi prices into DB")
    parser.add_argument(
        "--states",
        nargs="+",
        default=["Maharashtra"],
        help="List of states to ingest prices for (default: Maharashtra)",
    )
    parser.add_argument(
        "--crops",
        nargs="+",
        default=None,
        help="List of crops to ingest (default: all configured MVP crops)",
    )
    parser.add_argument(
        "--backfill-days",
        type=int,
        default=0,
        help="Number of days to attempt backfilling (0 for current snapshot)",
    )
    args = parser.parse_args()
    asyncio.run(run_ingestion(args.states, args.crops, args.backfill_days))

if __name__ == "__main__":
    main()
