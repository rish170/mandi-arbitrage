from decimal import Decimal
import json
from pathlib import Path
import pytest
from app.core.profit import calculate_net_profit, round_currency

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "validation_snapshot.json"

def load_snapshots():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

SNAPSHOTS = load_snapshots()

@pytest.mark.parametrize("s", SNAPSHOTS, ids=[f"scenario_{s['id']}_{s['commodity']}_{s['mandi_name']}" for s in SNAPSHOTS])
def test_scenario_accuracy_against_independent_snapshot(s):
    """
    Assert engine net_q agrees with independently calculated expected net_q within 0.5%.
    Uses frozen snapshot fixtures for complete offline determinism.
    """
    price_q = Decimal(s["price_q"])
    quality_cut_pct = Decimal(s["quality_cut_pct"])
    quantity_q = Decimal(s["quantity_q"])
    capacity_q = Decimal(s["vehicle_capacity_q"])
    rate_per_km = Decimal(s["vehicle_rate_per_km"])
    market_fee_pct = Decimal(s["market_fee_pct"])
    commission_pct = Decimal(s["commission_pct"])
    road_km = Decimal(s["road_km"])
    expected_net_q = Decimal(s["net_q"])

    res = calculate_net_profit(
        price_q=price_q,
        quality_cut_pct=quality_cut_pct,
        quantity_q=quantity_q,
        vehicle_capacity_q=capacity_q,
        vehicle_rate_per_km=rate_per_km,
        market_fee_pct=market_fee_pct,
        commission_pct=commission_pct,
        road_km=road_km,
        include_other_charges=False,
    )

    engine_net_q = round_currency(res.net_q)
    abs_err = abs(engine_net_q - expected_net_q)
    pct_err = float((abs_err / abs(expected_net_q)) * Decimal("100"))

    # Assert within 0.5% (strictly well within bounds)
    assert pct_err <= 0.5, (
        f"Scenario {s['id']} exceeded 0.5% error: "
        f"engine={engine_net_q}, expected={expected_net_q}, err={pct_err:.4f}%"
    )
    # Intermediate checks
    assert res.vehicles_needed == s["vehicles_needed"]
    assert round_currency(res.transport_total) == Decimal(s["transport_total"])
    assert round_currency(res.transport_q) == Decimal(s["transport_q"])

def test_five_percent_rule_template_logic():
    """
    Test asserting that realistic field variations (intraday auction price drift,
    rural route deviations) remain within the 5.0% error threshold.
    """
    baseline_s = SNAPSHOTS[0]
    nominal_price = Decimal(baseline_s["price_q"])
    nominal_km = Decimal(baseline_s["road_km"])
    expected_nominal_net = Decimal(baseline_s["net_q"])

    # Simulate +/- 2% road detour and +/- 1.5% price bidding fluctuation
    field_price = nominal_price * Decimal("1.015")
    field_km = nominal_km * Decimal("1.02")

    res = calculate_net_profit(
        price_q=field_price,
        quality_cut_pct=Decimal(baseline_s["quality_cut_pct"]),
        quantity_q=Decimal(baseline_s["quantity_q"]),
        vehicle_capacity_q=Decimal(baseline_s["vehicle_capacity_q"]),
        vehicle_rate_per_km=Decimal(baseline_s["vehicle_rate_per_km"]),
        market_fee_pct=Decimal(baseline_s["market_fee_pct"]),
        commission_pct=Decimal(baseline_s["commission_pct"]),
        road_km=field_km,
        include_other_charges=False,
    )

    abs_err = abs(res.net_q - expected_nominal_net)
    pct_err = float((abs_err / abs(expected_nominal_net)) * Decimal("100"))

    assert pct_err <= 5.0, f"Simulated field variation exceeded 5.0% limit: {pct_err:.2f}%"
