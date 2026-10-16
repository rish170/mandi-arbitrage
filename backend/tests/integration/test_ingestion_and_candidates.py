import asyncio
from datetime import date, timedelta
from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import func, select

from app.db import Base
from app.models import Mandi, Price
from app.services.datagov import DataGovClient, DataGovRecord
from app.services.ingest import ingest_prices_for_crops
from app.services.mandis import get_candidate_mandis
from scripts.seed_demo_history import seed_demo_history

class MockDataGovClient:
    def __init__(self, records):
        self.records = records

    async def fetch_records(self, state=None, commodity=None, page_size=500):
        if commodity:
            return [r for r in self.records if r.commodity.lower() == commodity.lower()]
        return self.records

@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_ingestion_idempotency(test_db: AsyncSession):
    # Seed 2 test mandis
    mandi1 = Mandi(
        id=1,
        state="Maharashtra",
        district="Pune",
        name="Pune APMC",
        lat=18.5204,
        lng=73.8567,
        geocode_source="test",
        needs_review=False,
    )
    mandi2 = Mandi(
        id=2,
        state="Maharashtra",
        district="Nashik",
        name="Lasalgaon",
        lat=20.1472,
        lng=74.2256,
        geocode_source="test",
        needs_review=False,
    )
    test_db.add_all([mandi1, mandi2])
    await test_db.commit()

    today = date(2026, 10, 16)
    mock_records = [
        DataGovRecord(
            state="Maharashtra",
            district="Pune",
            market="Pune APMC",
            commodity="Wheat",
            variety="Other",
            grade="FAQ",
            arrival_date=today,
            min_price=Decimal("2400"),
            modal_price=Decimal("2500"),
            max_price=Decimal("2600"),
        ),
        DataGovRecord(
            state="Maharashtra",
            district="Nashik",
            market="Lasalgaon",
            commodity="Onion",
            variety="Red",
            grade="FAQ",
            arrival_date=today,
            min_price=Decimal("1500"),
            modal_price=Decimal("1700"),
            max_price=Decimal("1900"),
        ),
    ]
    mock_client = MockDataGovClient(mock_records)

    # First run of ingestion
    res1 = await ingest_prices_for_crops(
        db=test_db,
        states=["Maharashtra"],
        crops=["Wheat", "Onion"],
        client=mock_client,
    )
    assert res1.inserted == 2
    assert res1.updated == 0

    count1 = (await test_db.execute(select(func.count(Price.id)))).scalar_one()
    assert count1 == 2

    # Second run with exact same mock records -> Must be 0 inserted, 2 updated (pure idempotency)
    res2 = await ingest_prices_for_crops(
        db=test_db,
        states=["Maharashtra"],
        crops=["Wheat", "Onion"],
        client=mock_client,
    )
    assert res2.inserted == 0
    assert res2.updated == 2

    count2 = (await test_db.execute(select(func.count(Price.id)))).scalar_one()
    assert count2 == 2

@pytest.mark.asyncio
async def test_get_candidate_mandis_distance_and_staleness(test_db: AsyncSession):
    # Origin at Pune center (18.5204, 73.8567)
    origin_lat, origin_lng = 18.5204, 73.8567
    today = date(2026, 10, 16)

    # Mandi 1: Pune APMC (approx 2 km away, fresh price)
    m1 = Mandi(
        id=10,
        state="Maharashtra",
        district="Pune",
        name="Pune Mandi",
        lat=18.5100,
        lng=73.8500,
        geocode_source="test",
        needs_review=False,
    )
    # Mandi 2: Baramati (approx 80 km away, fresh price)
    m2 = Mandi(
        id=20,
        state="Maharashtra",
        district="Pune",
        name="Baramati Mandi",
        lat=18.1517,
        lng=74.5772,
        geocode_source="test",
        needs_review=False,
    )
    # Mandi 3: Nagpur (approx 620 km away, out of 150 km radius)
    m3 = Mandi(
        id=30,
        state="Maharashtra",
        district="Nagpur",
        name="Nagpur Mandi",
        lat=21.1458,
        lng=79.0882,
        geocode_source="test",
        needs_review=False,
    )
    # Mandi 4: Shirur (approx 65 km away, STALE price: 10 days old)
    m4 = Mandi(
        id=40,
        state="Maharashtra",
        district="Pune",
        name="Shirur Mandi",
        lat=18.8256,
        lng=74.3789,
        geocode_source="test",
        needs_review=False,
    )

    test_db.add_all([m1, m2, m3, m4])
    await test_db.flush()

    # Add prices for Wheat
    p1 = Price(
        mandi_id=10,
        commodity="Wheat",
        arrival_date=today,
        modal_price=Decimal("2500"),
        is_seeded=False,
    )
    p2 = Price(
        mandi_id=20,
        commodity="Wheat",
        arrival_date=today - timedelta(days=1),
        modal_price=Decimal("2600"),
        is_seeded=False,
    )
    p3 = Price(
        mandi_id=30,
        commodity="Wheat",
        arrival_date=today,
        modal_price=Decimal("2700"),
        is_seeded=False,
    )
    p4 = Price(
        mandi_id=40,
        commodity="Wheat",
        arrival_date=today - timedelta(days=10),  # Stale (> 3 days)
        modal_price=Decimal("2450"),
        is_seeded=False,
    )

    test_db.add_all([p1, p2, p3, p4])
    await test_db.commit()

    candidates = await get_candidate_mandis(
        db=test_db,
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        commodity="Wheat",
        max_radius_km=150.0,
        max_age_days=3,
        reference_date=today,
    )

    # Expected: m1 and m2 only (m3 is out of radius, m4 has price > 3 days old)
    candidate_ids = [c[0].id for c in candidates]
    assert candidate_ids == [10, 20]  # Sorted by distance (m1 closest)
    assert candidates[0][2] < candidates[1][2]  # Dist 1 < Dist 2
