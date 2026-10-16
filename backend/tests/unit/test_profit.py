from decimal import Decimal
import pytest
from app.core.profit import calculate_net_profit, round_currency

def test_case_1_standard_baseline():
    """
    Case 1: Standard baseline
    - Quantity: 10 quintals
    - Price: 2400 Rs/q
    - Quality cut: 0%
    - Vehicle: pickup (capacity 15 q, rate 18 Rs/km)
    - Road distance: 10 km
    - Market fee: 1.0%, Commission: 2.0% (total 3.0%)
    - Other charges: False

    Arithmetic:
    quality_cut_q   = 2400 * 0% = 0.00
    realized_q      = 2400 - 0 = 2400.00
    mandi_fee_q     = 2400 * 3% = 72.00
    vehicles        = ceil(10 / 15) = 1
    transport_total = 1 * 18 * 10 * 1.0 = 180.00
    transport_q     = 180 / 10 = 18.00
    other_q         = 0.00
    net_q           = 2400 - 72 - 18 - 0 = 2310.00
    net_total       = 2310 * 10 = 23100.00
    """
    res = calculate_net_profit(
        price_q=Decimal("2400.00"),
        quality_cut_pct=Decimal("0.0"),
        quantity_q=Decimal("10.0"),
        vehicle_capacity_q=Decimal("15.0"),
        vehicle_rate_per_km=Decimal("18.0"),
        market_fee_pct=Decimal("1.0"),
        commission_pct=Decimal("2.0"),
        road_km=Decimal("10.0"),
        include_other_charges=False,
    )
    assert res.price_q == Decimal("2400.00")
    assert res.quality_cut_q == Decimal("0.00")
    assert res.realized_q == Decimal("2400.00")
    assert res.mandi_fee_q == Decimal("72.00")
    assert res.vehicles_needed == 1
    assert res.transport_total == Decimal("180.00")
    assert res.transport_q == Decimal("18.00")
    assert res.other_q == Decimal("0.00")
    assert res.net_q == Decimal("2310.00")
    assert res.net_total == Decimal("23100.00")

def test_case_2_average_quality_cut():
    """
    Case 2: Average quality cut (5%)
    - Price: 2400 Rs/q, 5% cut

    Arithmetic:
    quality_cut_q   = 2400 * 0.05 = 120.00
    realized_q      = 2400 - 120 = 2280.00
    mandi_fee_q     = 2280 * 0.03 = 68.40
    vehicles        = 1
    transport_total = 180.00, transport_q = 18.00
    other_q         = 0.00
    net_q           = 2280 - 68.40 - 18 - 0 = 2193.60
    net_total       = 2193.60 * 10 = 21936.00
    """
    res = calculate_net_profit(
        price_q=Decimal("2400.00"),
        quality_cut_pct=Decimal("5.0"),
        quantity_q=Decimal("10.0"),
        vehicle_capacity_q=Decimal("15.0"),
        vehicle_rate_per_km=Decimal("18.0"),
        market_fee_pct=Decimal("1.0"),
        commission_pct=Decimal("2.0"),
        road_km=Decimal("10.0"),
        include_other_charges=False,
    )
    assert res.quality_cut_q == Decimal("120.00")
    assert res.realized_q == Decimal("2280.00")
    assert res.mandi_fee_q == Decimal("68.40")
    assert res.net_q == Decimal("2193.60")
    assert res.net_total == Decimal("21936.00")

def test_case_3_poor_quality_cut():
    """
    Case 3: High quality cut (Poor quality 15%)
    - Price: 3000 Rs/q, 15% cut, road 20 km

    Arithmetic:
    quality_cut_q   = 3000 * 0.15 = 450.00
    realized_q      = 3000 - 450 = 2550.00
    mandi_fee_q     = 2550 * 0.03 = 76.50
    transport_total = 1 * 18 * 20 = 360.00, transport_q = 36.00
    net_q           = 2550 - 76.50 - 36 = 2437.50
    net_total       = 2437.50 * 10 = 24375.00
    """
    res = calculate_net_profit(
        price_q=Decimal("3000.00"),
        quality_cut_pct=Decimal("15.0"),
        quantity_q=Decimal("10.0"),
        vehicle_capacity_q=Decimal("15.0"),
        vehicle_rate_per_km=Decimal("18.0"),
        market_fee_pct=Decimal("1.0"),
        commission_pct=Decimal("2.0"),
        road_km=Decimal("20.0"),
        include_other_charges=False,
    )
    assert res.quality_cut_q == Decimal("450.00")
    assert res.realized_q == Decimal("2550.00")
    assert res.mandi_fee_q == Decimal("76.50")
    assert res.transport_q == Decimal("36.00")
    assert res.net_q == Decimal("2437.50")
    assert res.net_total == Decimal("24375.00")

def test_case_4_custom_high_quality_cut():
    """
    Case 4: Custom high quality cut (30%)
    - Price: 2000 Rs/q, 30% cut

    Arithmetic:
    quality_cut_q = 2000 * 0.30 = 600.00
    realized_q    = 2000 - 600 = 1400.00
    mandi_fee_q   = 1400 * 0.03 = 42.00
    transport_q   = 180 / 10 = 18.00
    net_q         = 1400 - 42 - 18 = 1340.00
    net_total     = 1340 * 10 = 13400.00
    """
    res = calculate_net_profit(
        price_q=Decimal("2000.00"),
        quality_cut_pct=Decimal("30.0"),
        quantity_q=Decimal("10.0"),
        vehicle_capacity_q=Decimal("15.0"),
        vehicle_rate_per_km=Decimal("18.0"),
        market_fee_pct=Decimal("1.0"),
        commission_pct=Decimal("2.0"),
        road_km=Decimal("10.0"),
        include_other_charges=False,
    )
    assert res.quality_cut_q == Decimal("600.00")
    assert res.realized_q == Decimal("1400.00")
    assert res.mandi_fee_q == Decimal("42.00")
    assert res.net_q == Decimal("1340.00")
    assert res.net_total == Decimal("13400.00")

def test_case_5_multi_vehicle_ceil_division():
    """
    Case 5: Multi-vehicle capacity edge case
    - 10 quintals on an 8 q tempo needs ceil(10 / 8) = 2 vehicles

    Arithmetic:
    vehicles_needed = ceil(10 / 8) = 2
    transport_total = 2 * 14 * 25 * 1.0 = 700.00
    transport_q     = 700 / 10 = 70.00
    realized_q      = 2500.00
    mandi_fee_q     = 2500 * 0.03 = 75.00
    net_q           = 2500 - 75 - 70 = 2355.00
    net_total       = 2355 * 10 = 23550.00
    """
    res = calculate_net_profit(
        price_q=Decimal("2500.00"),
        quality_cut_pct=Decimal("0.0"),
        quantity_q=Decimal("10.0"),
        vehicle_capacity_q=Decimal("8.0"),
        vehicle_rate_per_km=Decimal("14.0"),
        market_fee_pct=Decimal("1.0"),
        commission_pct=Decimal("2.0"),
        road_km=Decimal("25.0"),
        include_other_charges=False,
    )
    assert res.vehicles_needed == 2
    assert res.transport_total == Decimal("700.00")
    assert res.transport_q == Decimal("70.00")
    assert res.net_q == Decimal("2355.00")
    assert res.net_total == Decimal("23550.00")

def test_case_6_exact_vehicle_capacity():
    """
    Case 6: Exact multiple of vehicle capacity
    - 16 quintals on an 8 q tempo needs exactly 2 vehicles

    Arithmetic:
    vehicles_needed = ceil(16 / 8) = 2
    transport_total = 2 * 14 * 10 = 280.00
    transport_q     = 280 / 16 = 17.50
    realized_q      = 2000.00
    mandi_fee_q     = 2000 * 0.03 = 60.00
    net_q           = 2000 - 60 - 17.50 = 1922.50
    net_total       = 1922.50 * 16 = 30760.00
    """
    res = calculate_net_profit(
        price_q=Decimal("2000.00"),
        quality_cut_pct=Decimal("0.0"),
        quantity_q=Decimal("16.0"),
        vehicle_capacity_q=Decimal("8.0"),
        vehicle_rate_per_km=Decimal("14.0"),
        market_fee_pct=Decimal("1.0"),
        commission_pct=Decimal("2.0"),
        road_km=Decimal("10.0"),
        include_other_charges=False,
    )
    assert res.vehicles_needed == 2
    assert res.transport_total == Decimal("280.00")
    assert res.transport_q == Decimal("17.50")
    assert res.net_q == Decimal("1922.50")
    assert res.net_total == Decimal("30760.00")

def test_case_7_just_over_vehicle_capacity():
    """
    Case 7: Just over single vehicle capacity
    - 8.1 quintals on an 8 q tempo requires 2 vehicles

    Arithmetic:
    vehicles_needed = ceil(8.1 / 8) = 2
    transport_total = 2 * 14 * 20 = 560.00
    transport_q     = 560 / 8.1 = 69.135802...
    price_q         = 2200.00
    mandi_fee_q     = 2200 * 0.03 = 66.00
    net_q           = 2200 - 66 - (560 / 8.1) = 2064.864197...
    net_total       = net_q * 8.1 = (2134 * 8.1) - 560 = 17285.4 - 560 = 16725.40
    """
    res = calculate_net_profit(
        price_q=Decimal("2200.00"),
        quality_cut_pct=Decimal("0.0"),
        quantity_q=Decimal("8.1"),
        vehicle_capacity_q=Decimal("8.0"),
        vehicle_rate_per_km=Decimal("14.0"),
        market_fee_pct=Decimal("1.0"),
        commission_pct=Decimal("2.0"),
        road_km=Decimal("20.0"),
        include_other_charges=False,
    )
    assert res.vehicles_needed == 2
    assert res.transport_total == Decimal("560.00")
    assert round_currency(res.net_q) == Decimal("2064.86")
    assert round_currency(res.net_total) == Decimal("16725.40")

def test_case_8_other_charges_enabled():
    """
    Case 8: Miscellaneous charges enabled (loading/unloading 3 Rs/q + weighing 1 Rs/q = 4 Rs/q)
    
    Arithmetic:
    other_q   = 3.0 + 1.0 = 4.00
    net_q     = 2400 - 72 - 18 - 4 = 2306.00
    net_total = 2306 * 10 = 23060.00
    """
    res = calculate_net_profit(
        price_q=Decimal("2400.00"),
        quality_cut_pct=Decimal("0.0"),
        quantity_q=Decimal("10.0"),
        vehicle_capacity_q=Decimal("15.0"),
        vehicle_rate_per_km=Decimal("18.0"),
        market_fee_pct=Decimal("1.0"),
        commission_pct=Decimal("2.0"),
        road_km=Decimal("10.0"),
        include_other_charges=True,
        loading_unloading_q=Decimal("3.0"),
        weighing_q=Decimal("1.0"),
    )
    assert res.other_q == Decimal("4.00")
    assert res.net_q == Decimal("2306.00")
    assert res.net_total == Decimal("23060.00")

def test_case_9_other_charges_disabled():
    """
    Case 9: Miscellaneous charges disabled
    
    Arithmetic:
    other_q   = 0.00
    net_q     = 2400 - 72 - 18 - 0 = 2310.00
    net_total = 23100.00
    """
    res = calculate_net_profit(
        price_q=Decimal("2400.00"),
        quality_cut_pct=Decimal("0.0"),
        quantity_q=Decimal("10.0"),
        vehicle_capacity_q=Decimal("15.0"),
        vehicle_rate_per_km=Decimal("18.0"),
        market_fee_pct=Decimal("1.0"),
        commission_pct=Decimal("2.0"),
        road_km=Decimal("10.0"),
        include_other_charges=False,
    )
    assert res.other_q == Decimal("0.00")
    assert res.net_q == Decimal("2310.00")

def test_case_10_custom_fee_overrides():
    """
    Case 10: Fee and commission overrides
    - Fee: 1.5%, Commission: 2.5% (Total 4.0%)

    Arithmetic:
    realized_q  = 2000.00
    mandi_fee_q = 2000 * 0.04 = 80.00
    transport_q = 18.00
    net_q       = 2000 - 80 - 18 = 1902.00
    net_total   = 19020.00
    """
    res = calculate_net_profit(
        price_q=Decimal("2000.00"),
        quality_cut_pct=Decimal("0.0"),
        quantity_q=Decimal("10.0"),
        vehicle_capacity_q=Decimal("15.0"),
        vehicle_rate_per_km=Decimal("18.0"),
        market_fee_pct=Decimal("1.5"),
        commission_pct=Decimal("2.5"),
        road_km=Decimal("10.0"),
        include_other_charges=False,
    )
    assert res.mandi_fee_q == Decimal("80.00")
    assert res.net_q == Decimal("1902.00")
    assert res.net_total == Decimal("19020.00")

def test_case_11_zero_distance():
    """
    Case 11: Zero distance (farmer adjacent to mandi)
    
    Arithmetic:
    transport_total = 0.00
    transport_q     = 0.00
    net_q           = 2200 - 66 - 0 = 2134.00
    net_total       = 21340.00
    """
    res = calculate_net_profit(
        price_q=Decimal("2200.00"),
        quality_cut_pct=Decimal("0.0"),
        quantity_q=Decimal("10.0"),
        vehicle_capacity_q=Decimal("15.0"),
        vehicle_rate_per_km=Decimal("18.0"),
        market_fee_pct=Decimal("1.0"),
        commission_pct=Decimal("2.0"),
        road_km=Decimal("0.0"),
        include_other_charges=False,
    )
    assert res.transport_total == Decimal("0.0")
    assert res.transport_q == Decimal("0.0")
    assert res.net_q == Decimal("2134.00")
    assert res.net_total == Decimal("21340.00")

def test_case_12_negative_net_profit():
    """
    Case 12: Negative net profit (low price produce, long distance freight)
    - Price: 200 Rs/q, 300 km distance at 38 Rs/km for 10 q on 100 q truck

    Arithmetic:
    vehicles_needed = ceil(10 / 100) = 1
    transport_total = 1 * 38 * 300 = 11400.00
    transport_q     = 11400 / 10 = 1140.00
    realized_q      = 200.00
    mandi_fee_q     = 200 * 0.03 = 6.00
    net_q           = 200 - 6 - 1140 = -946.00
    net_total       = -946 * 10 = -9460.00
    """
    res = calculate_net_profit(
        price_q=Decimal("200.00"),
        quality_cut_pct=Decimal("0.0"),
        quantity_q=Decimal("10.0"),
        vehicle_capacity_q=Decimal("100.0"),
        vehicle_rate_per_km=Decimal("38.0"),
        market_fee_pct=Decimal("1.0"),
        commission_pct=Decimal("2.0"),
        road_km=Decimal("300.0"),
        include_other_charges=False,
    )
    assert res.net_q == Decimal("-946.00")
    assert res.net_total == Decimal("-9460.00")

def test_case_13_large_commercial_truck():
    """
    Case 13: Large volume commercial truck
    - Quantity: 100 quintals on 100 q truck, 100 km distance, other charges enabled

    Arithmetic:
    vehicles_needed = ceil(100 / 100) = 1
    transport_total = 1 * 38 * 100 = 3800.00
    transport_q     = 3800 / 100 = 38.00
    realized_q      = 2800.00
    mandi_fee_q     = 2800 * 0.03 = 84.00
    other_q         = 4.00
    net_q           = 2800 - 84 - 38 - 4 = 2674.00
    net_total       = 2674 * 100 = 267400.00
    """
    res = calculate_net_profit(
        price_q=Decimal("2800.00"),
        quality_cut_pct=Decimal("0.0"),
        quantity_q=Decimal("100.0"),
        vehicle_capacity_q=Decimal("100.0"),
        vehicle_rate_per_km=Decimal("38.0"),
        market_fee_pct=Decimal("1.0"),
        commission_pct=Decimal("2.0"),
        road_km=Decimal("100.0"),
        include_other_charges=True,
    )
    assert res.vehicles_needed == 1
    assert res.transport_q == Decimal("38.00")
    assert res.net_q == Decimal("2674.00")
    assert res.net_total == Decimal("267400.00")

def test_case_14_round_trip_factor():
    """
    Case 14: Round trip factor 2.0 (empty return freight)
    - Distance: 50 km, factor: 2.0

    Arithmetic:
    transport_total = 1 * 18 * 50 * 2.0 = 1800.00
    transport_q     = 1800 / 10 = 180.00
    realized_q      = 2500.00
    mandi_fee_q     = 2500 * 0.03 = 75.00
    net_q           = 2500 - 75 - 180 = 2245.00
    net_total       = 2245 * 10 = 22450.00
    """
    res = calculate_net_profit(
        price_q=Decimal("2500.00"),
        quality_cut_pct=Decimal("0.0"),
        quantity_q=Decimal("10.0"),
        vehicle_capacity_q=Decimal("15.0"),
        vehicle_rate_per_km=Decimal("18.0"),
        market_fee_pct=Decimal("1.0"),
        commission_pct=Decimal("2.0"),
        road_km=Decimal("50.0"),
        round_trip_factor=Decimal("2.0"),
        include_other_charges=False,
    )
    assert res.transport_total == Decimal("1800.00")
    assert res.transport_q == Decimal("180.00")
    assert res.net_q == Decimal("2245.00")
    assert res.net_total == Decimal("22450.00")

def test_case_15_invalid_quantity():
    """Case 15: Quantity <= 0 raises ValueError"""
    with pytest.raises(ValueError, match="Quantity must be greater than 0"):
        calculate_net_profit(
            price_q=Decimal("2400.00"),
            quality_cut_pct=Decimal("0.0"),
            quantity_q=Decimal("0.0"),
            vehicle_capacity_q=Decimal("15.0"),
            vehicle_rate_per_km=Decimal("18.0"),
            market_fee_pct=Decimal("1.0"),
            commission_pct=Decimal("2.0"),
            road_km=Decimal("10.0"),
        )

def test_case_16_missing_price_raises_error():
    """Case 16: None price raises ValueError"""
    with pytest.raises(ValueError, match="Mandi price cannot be None or missing"):
        calculate_net_profit(
            price_q=None,
            quality_cut_pct=Decimal("0.0"),
            quantity_q=Decimal("10.0"),
            vehicle_capacity_q=Decimal("15.0"),
            vehicle_rate_per_km=Decimal("18.0"),
            market_fee_pct=Decimal("1.0"),
            commission_pct=Decimal("2.0"),
            road_km=Decimal("10.0"),
        )

def test_case_17_negative_parameters():
    """Case 17: Negative road distance raises ValueError"""
    with pytest.raises(ValueError, match="Road distance cannot be negative"):
        calculate_net_profit(
            price_q=Decimal("2400.00"),
            quality_cut_pct=Decimal("0.0"),
            quantity_q=Decimal("10.0"),
            vehicle_capacity_q=Decimal("15.0"),
            vehicle_rate_per_km=Decimal("18.0"),
            market_fee_pct=Decimal("1.0"),
            commission_pct=Decimal("2.0"),
            road_km=Decimal("-10.0"),
        )
