from datetime import date
from decimal import Decimal
from app.services.datagov import DataGovRecord
from app.services.ingest import normalize_market_name, resolve_mandi_id

def test_normalize_market_name():
    assert normalize_market_name("APMC Chikali ") == "chikali"
    assert normalize_market_name("Pune APMC") == "pune"
    assert normalize_market_name("Sindi (Selu)") == "sindi selu"
    assert normalize_market_name("Nashik(Dindori)") == "nashik dindori"
    assert normalize_market_name("  Baramati, APMC.  ") == "baramati"

def test_resolve_mandi_id():
    exact_lookup = {
        ("maharashtra", "pune", "pune"): 1,
        ("maharashtra", "nashik", "lasalgaon"): 2,
    }
    state_lookup = {
        ("maharashtra", "pune"): 1,
        ("maharashtra", "lasalgaon"): 2,
    }

    # Record with APMC in name
    rec1 = DataGovRecord(
        state="Maharashtra",
        district="Pune",
        market="Pune APMC",
        commodity="Wheat",
        arrival_date=date(2026, 10, 16),
        modal_price=Decimal("2500"),
    )
    assert resolve_mandi_id(rec1, exact_lookup, state_lookup) == 1

    # Record with different casing/whitespace
    rec2 = DataGovRecord(
        state="maharashtra",
        district="Nashik",
        market="  LASALGAON  ",
        commodity="Onion",
        arrival_date=date(2026, 10, 16),
        modal_price=Decimal("1800"),
    )
    assert resolve_mandi_id(rec2, exact_lookup, state_lookup) == 2

    # Unmatched record
    rec3 = DataGovRecord(
        state="Maharashtra",
        district="Nagpur",
        market="Unknown Market",
        commodity="Cotton",
        arrival_date=date(2026, 10, 16),
        modal_price=Decimal("7000"),
    )
    assert resolve_mandi_id(rec3, exact_lookup, state_lookup) is None
