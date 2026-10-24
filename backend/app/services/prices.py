from datetime import date, timedelta
from decimal import Decimal
import logging
from typing import Dict, List, Optional, Tuple

from cachetools import TTLCache
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Price
from app.schemas import TrendPoint, TrendSeries

logger = logging.getLogger(__name__)

# In-memory TTL cache for prices (15 minutes TTL)
MEMORY_PRICE_CACHE: TTLCache = TTLCache(maxsize=5000, ttl=900)

class AggregatedMandiPrice:
    def __init__(
        self,
        mandi_id: int,
        commodity: str,
        modal_price: Decimal,
        min_price: Optional[Decimal],
        max_price: Optional[Decimal],
        arrival_date: date,
        age_days: int,
        variety: str,
        varieties_used: int,
        is_stale: bool,
    ):
        self.mandi_id = mandi_id
        self.commodity = commodity
        self.modal_price = modal_price
        self.min_price = min_price
        self.max_price = max_price
        self.arrival_date = arrival_date
        self.age_days = age_days
        self.variety = variety
        self.varieties_used = varieties_used
        self.is_stale = is_stale

async def get_latest_prices_for_mandis(
    db: AsyncSession,
    mandi_ids: List[int],
    commodity: str,
    variety: Optional[str] = None,
    reference_date: Optional[date] = None,
    max_age_days: int = 3,
) -> Tuple[Dict[int, AggregatedMandiPrice], bool]:
    """
    Fetch latest prices for candidate mandis within max_age_days.
    Checks 15-minute in-memory TTL cache first.
    Aggregates mean modal price across varieties if multiple exist on the latest date.
    Flags is_stale=True if age_days is 2 or 3.
    Excludes mandis with no price within max_age_days.
    Returns: (dict of AggregatedMandiPrice by mandi_id, all_cache_hit boolean)
    """
    ref_date = reference_date or date.today()
    min_date = ref_date - timedelta(days=max_age_days)

    out: Dict[int, AggregatedMandiPrice] = {}
    missing_ids: List[int] = []

    # 1. Check in-memory TTL cache
    for mid in mandi_ids:
        cache_key = (mid, commodity.lower(), variety.lower() if variety else None, ref_date)
        if cache_key in MEMORY_PRICE_CACHE:
            out[mid] = MEMORY_PRICE_CACHE[cache_key]
        else:
            missing_ids.append(mid)

    all_cache_hit = len(missing_ids) == 0 and len(mandi_ids) > 0

    # 2. Query DB for missing mandi prices
    if missing_ids:
        stmt = (
            select(Price)
            .where(
                Price.mandi_id.in_(missing_ids),
                func.lower(Price.commodity) == commodity.lower(),
                Price.arrival_date >= min_date,
            )
            .order_by(Price.mandi_id, Price.arrival_date.desc())
        )
        if variety:
            stmt = stmt.where(func.lower(Price.variety) == variety.lower())

        results = (await db.execute(stmt)).scalars().all()

        # Fallback if some mandis have prices older than min_date
        found_mandi_ids = {p.mandi_id for p in results}
        unresolved_ids = [mid for mid in missing_ids if mid not in found_mandi_ids]
        if unresolved_ids:
            fallback_stmt = (
                select(Price)
                .where(
                    Price.mandi_id.in_(unresolved_ids),
                    func.lower(Price.commodity) == commodity.lower(),
                )
                .order_by(Price.mandi_id, Price.arrival_date.desc())
            )
            if variety:
                fallback_stmt = fallback_stmt.where(func.lower(Price.variety) == variety.lower())
            fallback_results = (await db.execute(fallback_stmt)).scalars().all()
            results = list(results) + list(fallback_results)

        # Group prices by mandi_id -> list of prices on the LATEST arrival_date for that mandi
        mandi_latest_map: Dict[int, List[Price]] = {}
        for p in results:
            mid = p.mandi_id
            if mid not in mandi_latest_map:
                mandi_latest_map[mid] = [p]
            else:
                latest_date = mandi_latest_map[mid][0].arrival_date
                if p.arrival_date == latest_date:
                    mandi_latest_map[mid].append(p)

        for mid, prices_list in mandi_latest_map.items():
            latest_date = prices_list[0].arrival_date
            age_days = (ref_date - latest_date).days
            is_stale = age_days >= 2

            varieties_used = len(prices_list)
            # Average modal price
            avg_modal = sum(p.modal_price for p in prices_list) / Decimal(str(varieties_used))

            # Overall min and max
            valid_mins = [p.min_price for p in prices_list if p.min_price is not None]
            overall_min = min(valid_mins) if valid_mins else None

            valid_maxs = [p.max_price for p in prices_list if p.max_price is not None]
            overall_max = max(valid_maxs) if valid_maxs else None

            if varieties_used == 1:
                variety_label = prices_list[0].variety
            else:
                variety_label = f"Aggregated ({varieties_used} varieties)"

            agg = AggregatedMandiPrice(
                mandi_id=mid,
                commodity=commodity,
                modal_price=round(avg_modal, 2),
                min_price=round(overall_min, 2) if overall_min is not None else None,
                max_price=round(overall_max, 2) if overall_max is not None else None,
                arrival_date=latest_date,
                age_days=age_days,
                variety=variety_label,
                varieties_used=varieties_used,
                is_stale=is_stale,
            )
            out[mid] = agg
            cache_key = (mid, commodity.lower(), variety.lower() if variety else None, ref_date)
            MEMORY_PRICE_CACHE[cache_key] = agg

    return out, all_cache_hit

async def get_trend_for_mandis(
    db: AsyncSession,
    mandi_ids: List[int],
    mandi_names: Dict[int, str],
    commodity: str,
    days: int = 7,
    reference_date: Optional[date] = None,
) -> List[TrendSeries]:
    """
    Returns daily price points for each mandi over the past `days` period.
    Missing days remain None (gaps are never interpolated).
    """
    ref_date = reference_date or date.today()
    start_date = ref_date - timedelta(days=days - 1)

    stmt = (
        select(Price)
        .where(
            Price.mandi_id.in_(mandi_ids),
            func.lower(Price.commodity) == commodity.lower(),
            Price.arrival_date >= start_date,
            Price.arrival_date <= ref_date,
        )
        .order_by(Price.mandi_id, Price.arrival_date.asc())
    )
    records = (await db.execute(stmt)).scalars().all()

    # If no records in current window, anchor to latest arrival date for these mandis
    if not records and mandi_ids:
        stmt_max = select(func.max(Price.arrival_date)).where(
            Price.mandi_id.in_(mandi_ids),
            func.lower(Price.commodity) == commodity.lower(),
        )
        max_d = (await db.execute(stmt_max)).scalar_one_or_none()
        if max_d:
            ref_date = max_d
            start_date = ref_date - timedelta(days=days - 1)
            stmt = (
                select(Price)
                .where(
                    Price.mandi_id.in_(mandi_ids),
                    func.lower(Price.commodity) == commodity.lower(),
                    Price.arrival_date >= start_date,
                    Price.arrival_date <= ref_date,
                )
                .order_by(Price.mandi_id, Price.arrival_date.asc())
            )
            records = (await db.execute(stmt)).scalars().all()

    # Index by (mandi_id, arrival_date) -> Price
    price_map: Dict[Tuple[int, date], Price] = {}
    for p in records:
        key = (p.mandi_id, p.arrival_date)
        if key not in price_map or p.is_seeded is False:
            price_map[key] = p

    series_list: List[TrendSeries] = []
    for mid in mandi_ids:
        points: List[TrendPoint] = []
        for i in range(days):
            target_d = start_date + timedelta(days=i)
            p = price_map.get((mid, target_d))
            if p:
                points.append(
                    TrendPoint(
                        date=target_d,
                        modal=p.modal_price,
                        min=p.min_price,
                        max=p.max_price,
                        is_seeded=p.is_seeded,
                    )
                )
            else:
                points.append(
                    TrendPoint(
                        date=target_d,
                        modal=None,
                        min=None,
                        max=None,
                        is_seeded=False,
                    )
                )

        series_list.append(
            TrendSeries(
                mandi_id=mid,
                mandi_name=mandi_names.get(mid, f"Mandi {mid}"),
                points=points,
            )
        )

    return series_list
