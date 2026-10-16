from decimal import Decimal
from app.config_loader import load_crops_config, load_rates_config

def test_load_rates_config():
    rates = load_rates_config()
    assert rates.status == "ASSUMPTION_UNVERIFIED"
    assert "No field survey" in rates.note
    assert rates.market_fee_pct_default == Decimal("1.0")
    assert rates.commission_pct_default == Decimal("2.0")

    # Check vehicle definitions
    assert "tempo" in rates.vehicles
    assert rates.vehicles["tempo"].capacity_quintals == Decimal("8")
    assert rates.vehicles["tempo"].rate_per_km == Decimal("14.0")

    assert "pickup" in rates.vehicles
    assert rates.vehicles["pickup"].capacity_quintals == Decimal("15")
    assert rates.vehicles["pickup"].rate_per_km == Decimal("18.0")

    assert "mini_truck" in rates.vehicles
    assert rates.vehicles["mini_truck"].capacity_quintals == Decimal("40")
    assert rates.vehicles["mini_truck"].rate_per_km == Decimal("26.0")

    assert "truck" in rates.vehicles
    assert rates.vehicles["truck"].capacity_quintals == Decimal("100")
    assert rates.vehicles["truck"].rate_per_km == Decimal("38.0")

    # Check quality grades
    assert rates.quality_grades["Good"] == Decimal("0.0")
    assert rates.quality_grades["Average"] == Decimal("5.0")
    assert rates.quality_grades["Below Average"] == Decimal("10.0")
    assert rates.quality_grades["Poor"] == Decimal("15.0")

    # Check other charges
    assert rates.other_charges_per_quintal["loading_unloading"] == Decimal("3.0")
    assert rates.other_charges_per_quintal["weighing"] == Decimal("1.0")

    # Check fallback distance
    assert rates.fallback_distance["road_factor"] == Decimal("1.3")
    assert rates.fallback_distance["average_speed_kmh"] == Decimal("40.0")

def test_load_crops_config():
    crops_cfg = load_crops_config()
    assert len(crops_cfg.crops) == 7

    crop_names = [c.name_en for c in crops_cfg.crops]
    expected_crops = [
        "Wheat",
        "Rice (Paddy)",
        "Soyabean",
        "Cotton",
        "Onion",
        "Potato",
        "Tomato",
    ]
    for expected in expected_crops:
        assert expected in crop_names

    # Check Hindi names and aliases exist
    for crop in crops_cfg.crops:
        assert len(crop.name_hi) > 0
        assert len(crop.aliases) > 0
