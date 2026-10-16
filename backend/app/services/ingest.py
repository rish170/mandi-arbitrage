import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.config_loader import load_crops_config
from app.models import Mandi, Price
from app.services.datagov import DataGovClient, DataGovRecord

logger = logging.getLogger(__name__)

def normalize_market_name(name: str) -> str:
    """Normalize market names by casefolding, removing APMC and stripping punctuation."""
    s = name.lower()
    s = re.sub(r"\bapmc\b", " ", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

class IngestionResult:
    def __init__(self):
        self.total_fetched: int = 0
        self.inserted: int = 0
        self.updated: int = 0
        self.unmatched_markets: List[Dict[str, Any]] = []
        self.start_time: datetime = datetime.now(timezone.utc)
        self.end_time: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        end = self.end_time or datetime.now(timezone.utc)
        return (end - self.start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": "success",
            "records_fetched": self.total_fetched,
            "records_inserted": self.inserted,
            "records_updated": self.updated,
            "unmatched_count": len(self.unmatched_markets),
            "unmatched_sample": self.unmatched_markets[:10],
            "duration_seconds": round(self.duration_seconds, 2),
        }

async def build_mandi_lookup(
    db: AsyncSession, state: Optional[str] = None
) -> Tuple[Dict[Tuple[str, str, str], int], Dict[Tuple[str, str], int]]:
    """
    Build in-memory fast lookups for Mandi ID resolution:
    1. (state_lower, district_lower, normalized_name) -> mandi_id
    2. (state_lower, normalized_name) -> mandi_id (district-fallback)
    """
    stmt = select(Mandi)
    if state:
        stmt = stmt.where(func.lower(Mandi.state) == state.lower())
    mandis = (await db.execute(stmt)).scalars().all()

    exact_lookup: Dict[Tuple[str, str, str], int] = {}
    state_lookup: Dict[Tuple[str, str], int] = {}

    for m in mandis:
        s_low = m.state.lower().strip()
        d_low = m.district.lower().strip()
        norm_name = normalize_market_name(m.name)

        exact_lookup[(s_low, d_low, norm_name)] = m.id
        if (s_low, norm_name) not in state_lookup:
            state_lookup[(s_low, norm_name)] = m.id

    return exact_lookup, state_lookup

def resolve_mandi_id(
    record: DataGovRecord,
    exact_lookup: Dict[Tuple[str, str, str], int],
    state_lookup: Dict[Tuple[str, str], int],
) -> Optional[int]:
    s_low = record.state.lower().strip()
    d_low = record.district.lower().strip()
    norm_name = normalize_market_name(record.market)

    # 1. Exact match on (state, district, normalized_name)
    m_id = exact_lookup.get((s_low, d_low, norm_name))
    if m_id:
        return m_id

    # 2. Match on (state, normalized_name)
    m_id = state_lookup.get((s_low, norm_name))
    if m_id:
        return m_id

    # 3. Partial / token subset match on normalized_name in same district
    for (st, dist, name), candidate_id in exact_lookup.items():
        if st == s_low and dist == d_low:
            if norm_name in name or name in norm_name:
                return candidate_id

    return None

async def ingest_prices_for_crops(
    db: AsyncSession,
    states: Optional[List[str]] = None,
    crops: Optional[List[str]] = None,
    client: Optional[DataGovClient] = None,
) -> IngestionResult:
    result = IngestionResult()
    target_states = states or ["Maharashtra"]
    datagov = client or DataGovClient()

    crops_cfg = load_crops_config()
    target_crops_list = crops_cfg.crops
    if crops:
        crop_names_low = [c.lower() for c in crops]
        target_crops_list = [
            c for c in target_crops_list if c.name_en.lower() in crop_names_low
        ]

    for state in target_states:
        exact_lookup, state_lookup = await build_mandi_lookup(db, state=state)
        logger.info(f"Loaded {len(exact_lookup)} mandis for price matching in {state}")

        for crop in target_crops_list:
            # Query data.gov.in using primary name and aliases
            commodities_to_fetch = [crop.name_en] + [
                a for a in crop.aliases if a != crop.name_en
            ]

            fetched_records: List[DataGovRecord] = []
            for comm in commodities_to_fetch:
                try:
                    recs = await datagov.fetch_records(
                        state=state, commodity=comm, page_size=200
                    )
                    fetched_records.extend(recs)
                except Exception as e:
                    logger.warning(
                        f"Failed fetching {comm} in {state} from data.gov.in: {e}"
                    )

            result.total_fetched += len(fetched_records)

            for rec in fetched_records:
                mandi_id = resolve_mandi_id(rec, exact_lookup, state_lookup)
                if not mandi_id:
                    result.unmatched_markets.append(
                        {
                            "state": rec.state,
                            "district": rec.district,
                            "market": rec.market,
                            "commodity": rec.commodity,
                        }
                    )
                    continue

                # Standardize commodity to canonical English name
                canonical_commodity = crop.name_en

                # Upsert into Price table
                stmt = select(Price).where(
                    Price.mandi_id == mandi_id,
                    Price.commodity == canonical_commodity,
                    Price.variety == rec.variety,
                    Price.grade == rec.grade,
                    Price.arrival_date == rec.arrival_date,
                )
                existing = (await db.execute(stmt)).scalar_one_or_none()

                if existing:
                    existing.min_price = rec.min_price
                    existing.modal_price = rec.modal_price
                    existing.max_price = rec.max_price
                    existing.source = "data.gov.in"
                    existing.is_seeded = False
                    result.updated += 1
                else:
                    new_price = Price(
                        mandi_id=mandi_id,
                        commodity=canonical_commodity,
                        variety=rec.variety,
                        grade=rec.grade,
                        arrival_date=rec.arrival_date,
                        min_price=rec.min_price,
                        modal_price=rec.modal_price,
                        max_price=rec.max_price,
                        source="data.gov.in",
                        is_seeded=False,
                    )
                    db.add(new_price)
                    result.inserted += 1

        await db.commit()

    result.end_time = datetime.now(timezone.utc)
    logger.info(
        f"Ingestion completed: {result.inserted} inserted, {result.updated} updated, "
        f"{len(result.unmatched_markets)} unmatched in {result.duration_seconds:.2f}s"
    )
    return result
