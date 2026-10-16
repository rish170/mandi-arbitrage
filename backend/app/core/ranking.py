from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Tuple
from app.core.profit import ProfitBreakdown, round_currency

@dataclass
class MandiComparisonItem:
    mandi_id: int
    name: str
    district: str
    state: str
    lat: float
    lng: float
    road_km: float
    duration_min: float
    distance_source: str
    price_basis: str
    price_val: Decimal
    min_price: Decimal | None
    max_price: Decimal | None
    arrival_date: Any
    age_days: int
    variety: str
    varieties_used: int
    is_stale: bool
    breakdown: ProfitBreakdown

@dataclass
class RankedMandiResult:
    rank: int
    is_nearest: bool
    mandi: Dict[str, Any]
    price: Dict[str, Any]
    distance: Dict[str, Any]
    breakdown: Dict[str, Decimal]
    vs_nearest: Dict[str, Decimal]
    raw_item: MandiComparisonItem

@dataclass
class ComparisonSummary:
    best_mandi_id: int
    nearest_mandi_id: int
    extra_profit_q: Decimal
    extra_profit_total: Decimal

def rank_and_summarize(
    items: List[MandiComparisonItem], quantity_q: Decimal
) -> Tuple[List[RankedMandiResult], ComparisonSummary]:
    """
    Ranks comparison items by net_q descending (tie-break: smaller road_km).
    Identifies the nearest mandi by road_km.
    Computes delta_vs_nearest for each mandi and overall summary.
    """
    if not items:
        raise ValueError("Cannot rank empty list of mandis.")

    # 1. Identify nearest mandi by road_km
    nearest_item = min(items, key=lambda x: x.road_km)
    nearest_mandi_id = nearest_item.mandi_id
    nearest_net_q = nearest_item.breakdown.net_q

    # 2. Sort by net_q descending, tie-break smaller road_km ascending
    sorted_items = sorted(
        items,
        key=lambda x: (-x.breakdown.net_q, x.road_km),
    )

    best_item = sorted_items[0]
    best_mandi_id = best_item.mandi_id
    extra_profit_q = best_item.breakdown.net_q - nearest_net_q
    extra_profit_total = extra_profit_q * quantity_q

    summary = ComparisonSummary(
        best_mandi_id=best_mandi_id,
        nearest_mandi_id=nearest_mandi_id,
        extra_profit_q=round_currency(extra_profit_q),
        extra_profit_total=round_currency(extra_profit_total),
    )

    ranked_results: List[RankedMandiResult] = []
    for rank_idx, itm in enumerate(sorted_items, 1):
        delta_q = itm.breakdown.net_q - nearest_net_q
        delta_total = delta_q * quantity_q

        res = RankedMandiResult(
            rank=rank_idx,
            is_nearest=(itm.mandi_id == nearest_mandi_id),
            mandi={
                "id": itm.mandi_id,
                "name": itm.name,
                "district": itm.district,
                "state": itm.state,
                "lat": itm.lat,
                "lng": itm.lng,
            },
            price={
                "basis": itm.price_basis,
                "value": round_currency(itm.price_val),
                "min": round_currency(itm.min_price) if itm.min_price is not None else None,
                "max": round_currency(itm.max_price) if itm.max_price is not None else None,
                "arrival_date": itm.arrival_date,
                "age_days": itm.age_days,
                "variety": itm.variety,
                "varieties_used": itm.varieties_used,
                "is_stale": itm.is_stale,
            },
            distance={
                "road_km": round(itm.road_km, 2),
                "duration_min": round(itm.duration_min, 1),
                "source": itm.distance_source,
            },
            breakdown=itm.breakdown.to_rounded_dict(),
            vs_nearest={
                "delta_q": round_currency(delta_q),
                "delta_total": round_currency(delta_total),
            },
            raw_item=itm,
        )
        ranked_results.append(res)

    return ranked_results, summary
