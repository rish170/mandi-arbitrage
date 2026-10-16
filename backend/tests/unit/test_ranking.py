from decimal import Decimal
import pytest
from app.core.profit import ProfitBreakdown
from app.core.ranking import MandiComparisonItem, rank_and_summarize

def create_item(
    mandi_id: int,
    name: str,
    road_km: float,
    net_q: Decimal,
    price_val: Decimal = Decimal("2400.00"),
) -> MandiComparisonItem:
    breakdown = ProfitBreakdown(
        price_q=price_val,
        quality_cut_q=Decimal("0.00"),
        realized_q=price_val,
        mandi_fee_q=Decimal("72.00"),
        transport_q=Decimal("18.00"),
        other_q=Decimal("0.00"),
        net_q=net_q,
        net_total=net_q * Decimal("10.0"),
        vehicles_needed=1,
        transport_total=Decimal("180.00"),
    )
    return MandiComparisonItem(
        mandi_id=mandi_id,
        name=name,
        district="Nagpur",
        state="Maharashtra",
        lat=21.1458,
        lng=79.0882,
        road_km=road_km,
        duration_min=15.0,
        distance_source="routes_api",
        price_basis="modal",
        price_val=price_val,
        min_price=Decimal("2300.00"),
        max_price=Decimal("2500.00"),
        arrival_date="2026-10-15",
        age_days=1,
        variety="Lokwan",
        varieties_used=1,
        is_stale=False,
        breakdown=breakdown,
    )

def test_ranking_by_net_q_descending():
    """Verify items are sorted by net_q descending."""
    m1 = create_item(mandi_id=1, name="Mandi A", road_km=10.0, net_q=Decimal("2100.00"))
    m2 = create_item(mandi_id=2, name="Mandi B", road_km=25.0, net_q=Decimal("2350.00"))
    m3 = create_item(mandi_id=3, name="Mandi C", road_km=15.0, net_q=Decimal("2200.00"))

    ranked, summary = rank_and_summarize([m1, m2, m3], quantity_q=Decimal("10.0"))

    assert len(ranked) == 3
    # Mandi B has highest net_q (2350)
    assert ranked[0].mandi["id"] == 2
    assert ranked[0].rank == 1
    # Mandi C has second highest (2200)
    assert ranked[1].mandi["id"] == 3
    assert ranked[1].rank == 2
    # Mandi A has lowest (2100)
    assert ranked[2].mandi["id"] == 1
    assert ranked[2].rank == 3

    # Nearest is Mandi A (10 km)
    assert summary.nearest_mandi_id == 1
    assert ranked[2].is_nearest is True
    assert ranked[0].is_nearest is False

    # Best is Mandi B (2350 vs 2100 nearest)
    assert summary.best_mandi_id == 2
    assert summary.extra_profit_q == Decimal("250.00")
    assert summary.extra_profit_total == Decimal("2500.00")

def test_tie_breaking_by_smaller_road_km():
    """When net_q is equal, smaller road_km should rank higher."""
    m1 = create_item(mandi_id=1, name="Mandi Far", road_km=40.0, net_q=Decimal("2200.00"))
    m2 = create_item(mandi_id=2, name="Mandi Close", road_km=15.0, net_q=Decimal("2200.00"))

    ranked, summary = rank_and_summarize([m1, m2], quantity_q=Decimal("10.0"))

    assert ranked[0].mandi["id"] == 2
    assert ranked[0].distance["road_km"] == 15.0
    assert ranked[1].mandi["id"] == 1
    assert ranked[1].distance["road_km"] == 40.0

def test_vs_nearest_deltas():
    """Verify delta_q and delta_total are computed accurately against nearest mandi."""
    # Nearest mandi is ID 1 (road 5 km, net 2000)
    m1 = create_item(mandi_id=1, name="Near Mandi", road_km=5.0, net_q=Decimal("2000.00"))
    # Distant mandi is ID 2 (road 50 km, net 2250)
    m2 = create_item(mandi_id=2, name="Far Mandi", road_km=50.0, net_q=Decimal("2250.00"))

    ranked, summary = rank_and_summarize([m1, m2], quantity_q=Decimal("20.0"))

    # For m2: delta_q = 2250 - 2000 = 250, delta_total = 250 * 20 = 5000
    assert ranked[0].mandi["id"] == 2
    assert ranked[0].vs_nearest["delta_q"] == Decimal("250.00")
    assert ranked[0].vs_nearest["delta_total"] == Decimal("5000.00")

    # For m1 (the nearest itself): delta_q = 0, delta_total = 0
    assert ranked[1].mandi["id"] == 1
    assert ranked[1].vs_nearest["delta_q"] == Decimal("0.00")
    assert ranked[1].vs_nearest["delta_total"] == Decimal("0.00")

def test_empty_list_raises_value_error():
    """Ranking an empty list must raise ValueError."""
    with pytest.raises(ValueError, match="Cannot rank empty list"):
        rank_and_summarize([], quantity_q=Decimal("10.0"))
