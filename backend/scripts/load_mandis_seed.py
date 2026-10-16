"""Utility script to load mandi registry and initial prices from data/*.seed.json into the target database.
Safe and idempotent: updates existing coordinates or inserts missing mandis.
"""
import asyncio
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import async_session_factory
from app.models import Price
from app.services.mandis import load_seed_into_db

async def load_prices_seed_if_needed(session: AsyncSession) -> int:
    prices_path = BACKEND_DIR / "data" / "prices.seed.json"
    if not prices_path.exists():
        return 0

    # Check existing count
    count = (await session.execute(select(func.count(Price.id)))).scalar_one()
    if count >= 100:
        print(f"Prices already present in database ({count} records). Skipping price seed.")
        return 0

    with open(prices_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    inserted = 0
    for r in records:
        arrival_d = date.fromisoformat(r["arrival_date"]) if isinstance(r["arrival_date"], str) else r["arrival_date"]
        session.add(Price(
            mandi_id=r["mandi_id"],
            commodity=r["commodity"],
            variety=r.get("variety"),
            grade=r.get("grade"),
            arrival_date=arrival_d,
            min_price=Decimal(str(r["min_price"])) if r.get("min_price") is not None else None,
            max_price=Decimal(str(r["max_price"])) if r.get("max_price") is not None else None,
            modal_price=Decimal(str(r["modal_price"])),
            is_seeded=bool(r.get("is_seeded", False)),
            source=r.get("source", "seed"),
        ))
        inserted += 1

    if inserted > 0:
        await session.commit()

    return inserted

async def main():
    print("Loading mandis from seed file into database...")
    async with async_session_factory() as session:
        mandi_count = await load_seed_into_db(session)
        price_count = await load_prices_seed_if_needed(session)

    print(f"Successfully processed {mandi_count} mandis and {price_count} price records into database.")

if __name__ == "__main__":
    asyncio.run(main())
