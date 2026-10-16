"""Utility script to load mandi registry from data/mandis.seed.json into the target database.
Safe and idempotent: updates existing coordinates or inserts missing mandis.
"""
import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db import async_session_factory
from app.services.mandis import load_seed_into_db

async def main():
    print("Loading mandis from seed file into database...")
    async with async_session_factory() as session:
        async with session.begin():
            count = await load_seed_into_db(session)
    print(f"Successfully processed {count} mandis from seed file into database.")

if __name__ == "__main__":
    asyncio.run(main())
