import argparse
import asyncio
from datetime import date, timedelta
from decimal import Decimal
import logging
from pathlib import Path
import random
import sys

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.config import settings
from app.db import async_session_factory
from app.models import Price

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

async def seed_demo_history(force: bool = False, days_back: int = 6):
    if settings.ENV == "production" and not force:
        logger.error("Refusing to run demo history seeding in production environment without --force flag!")
        sys.exit(1)

    rng = random.Random(42)  # Fixed seed for deterministic demo history

    async with async_session_factory() as db:
        # 1. Fetch all real (non-seeded) prices
        stmt = select(Price).where(Price.is_seeded == False).order_by(Price.arrival_date.desc())
        result = await db.execute(stmt)
        real_prices = result.scalars().all()

        if not real_prices:
            logger.warning("No real price records found in DB to base demo history upon. Run price ingestion first.")
            return

        # Group by (mandi_id, commodity, variety, grade) and take the latest real price
        latest_groups = {}
        for p in real_prices:
            key = (p.mandi_id, p.commodity, p.variety, p.grade)
            if key not in latest_groups:
                latest_groups[key] = p

        logger.info(f"Found {len(latest_groups)} mandi-crop series with real price anchors.")

        seeded_count = 0
        for (mandi_id, commodity, variety, grade), anchor in latest_groups.items():
            base_modal = anchor.modal_price
            base_min = anchor.min_price or (base_modal * Decimal("0.95"))
            base_max = anchor.max_price or (base_modal * Decimal("1.05"))
            anchor_date = anchor.arrival_date

            curr_modal = base_modal
            curr_min = base_min
            curr_max = base_max

            for i in range(1, days_back + 1):
                past_date = anchor_date - timedelta(days=i)

                # Check if a real row already exists for this date
                check_stmt = select(Price).where(
                    Price.mandi_id == mandi_id,
                    Price.commodity == commodity,
                    Price.variety == variety,
                    Price.grade == grade,
                    Price.arrival_date == past_date,
                )
                existing = (await db.execute(check_stmt)).scalar_one_or_none()

                if existing and not existing.is_seeded:
                    # Never overwrite real rows
                    curr_modal = existing.modal_price
                    curr_min = existing.min_price or (curr_modal * Decimal("0.95"))
                    curr_max = existing.max_price or (curr_modal * Decimal("1.05"))
                    continue

                # Bounded random walk: -2% to +2% per day
                walk_factor = Decimal(str(round(rng.uniform(0.98, 1.02), 4)))
                curr_modal = round(curr_modal * walk_factor, 2)
                curr_min = round(curr_min * walk_factor, 2)
                curr_max = round(curr_max * walk_factor, 2)

                if existing and existing.is_seeded:
                    existing.modal_price = curr_modal
                    existing.min_price = curr_min
                    existing.max_price = curr_max
                    existing.source = "demo_seed"
                    seeded_count += 1
                elif not existing:
                    new_seeded = Price(
                        mandi_id=mandi_id,
                        commodity=commodity,
                        variety=variety,
                        grade=grade,
                        arrival_date=past_date,
                        modal_price=curr_modal,
                        min_price=curr_min,
                        max_price=curr_max,
                        source="demo_seed",
                        is_seeded=True,
                    )
                    db.add(new_seeded)
                    seeded_count += 1

        await db.commit()

        print("\n" + "=" * 50)
        print("DEMO HISTORY SEEDING SUMMARY")
        print("=" * 50)
        print(f"Mandi-Crop Series Anchored : {len(latest_groups)}")
        print(f"Historical Points Seeded   : {seeded_count}")
        print(f"Flagged is_seeded          : True (source='demo_seed')")
        print("=" * 50 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Seed bounded random walk demo history for trend series")
    parser.add_argument("--force", action="store_true", help="Force execution even if ENV=production")
    parser.add_argument("--days", type=int, default=6, help="Number of historical days to generate (default: 6)")
    args = parser.parse_args()
    asyncio.run(seed_demo_history(force=args.force, days_back=args.days))

if __name__ == "__main__":
    main()
