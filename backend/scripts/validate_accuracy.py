import argparse
import asyncio
import csv
import math
import sys
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

ROOT_DIR = BACKEND_DIR.parent
CSV_PATH = BACKEND_DIR / "data" / "validation" / "scenarios.csv"
DOCS_VALIDATION_PATH = ROOT_DIR / "docs" / "VALIDATION.md"

from sqlalchemy import select
from app.config_loader import load_rates_config
from app.core.geo import haversine_fallback_distance_km
from app.core.profit import calculate_net_profit, round_currency
from app.db import async_session_factory
from app.models import Mandi
from app.services.geocode import GeocodingService
from app.services.prices import get_latest_prices_for_mandis

def independent_straight_line_net_q(
    price: Decimal,
    cut_pct: Decimal,
    qty: Decimal,
    veh_cap: Decimal,
    veh_rate: Decimal,
    fee_pct: Decimal,
    comm_pct: Decimal,
    road_km: Decimal,
    round_trip: Decimal = Decimal("1.0"),
    include_other: bool = False,
    loading_unloading: Decimal = Decimal("3.0"),
    weighing: Decimal = Decimal("1.0"),
) -> Decimal:
    """
    Completely independent straight-line implementation of the Mandi Arbitrage
    Net Profit Formula. Shares zero code and imports with app.core.profit.
    """
    quality_cut = price * (cut_pct / Decimal("100"))
    realized = price - quality_cut
    statutory_fees = realized * ((fee_pct + comm_pct) / Decimal("100"))
    
    # Integer ceiling division for transport vehicles
    vehicles_needed = math.ceil(float(qty) / float(veh_cap))
    transport_total = Decimal(vehicles_needed) * veh_rate * road_km * round_trip
    transport_per_q = transport_total / qty
    
    other_per_q = (loading_unloading + weighing) if include_other else Decimal("0.0")
    
    net_per_q = realized - statutory_fees - transport_per_q - other_per_q
    return net_per_q

def generate_validation_markdown(
    rows: List[Dict[str, str]],
    results: Optional[List[Dict[str, any]]] = None,
    mean_error: Optional[float] = None,
    max_error: Optional[float] = None,
) -> str:
    md = []
    md.append("# Mandi Arbitrage Accuracy Validation Report\n")
    md.append("This document records the empirical validation of the net profit calculation engine against manual field calculations across 10 real-world agricultural trading scenarios.\n")
    md.append("## How to Complete Manual Scenario Validation\n")
    md.append("To validate the engine against external ground truth:\n")
    md.append("1. Open `backend/data/validation/scenarios.csv`.")
    md.append("2. For each scenario row:\n")
    md.append("   - **`manual_price_q`**: Check the official published modal price on Agmarknet/eNAM or data.gov.in for that mandi.")
    md.append("   - **`manual_road_km`**: Measure driving distance in Google Maps from the origin pincode centroid to the target APMC Mandi.")
    md.append("   - **`manual_fee_pct` & `manual_commission_pct`**: Verify local APMC mandi cess (e.g. 1.0% cess, 2.0% commission agent charge).")
    md.append("   - **`manual_rate_per_km`**: Enter prevailing commercial transport freight rate for the vehicle type (e.g. ₹14/km tempo, ₹18/km pickup, ₹26/km mini truck, ₹38/km truck).")
    md.append("   - **`manual_net_q`**: Independently calculate net profit using a standard handheld calculator or spreadsheet:")
    md.append("     $$\\text{Realized} = \\text{Price} \\times (1 - \\text{QualityCut})$$")
    md.append("     $$\\text{Fees} = \\text{Realized} \\times (\\text{Fee} + \\text{Commission})$$")
    md.append("     $$\\text{Transport} = \\frac{\\lceil \\text{Qty} / \\text{Cap} \\rceil \\times \\text{Rate} \\times \\text{Km}}{\\text{Qty}}$$")
    md.append("     $$\\text{Net} = \\text{Realized} - \\text{Fees} - \\text{Transport} - \\text{Other}$$")
    md.append("3. Re-run `python backend/scripts/validate_accuracy.py`.\n")

    md.append("## Validation Results (10 Scenarios)\n")
    if results and len(results) == 10:
        md.append("| ID | Origin | Commodity | Quantity (q) | Vehicle | Grade | Mandi | Engine Net (₹/q) | Manual Net (₹/q) | Abs Error (₹) | % Error | Status |")
        md.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in results:
            md.append(f"| {r['id']} | {r['origin']} | {r['commodity']} | {r['qty']} | {r['vehicle']} | {r['grade']} | {r['mandi']} | ₹{r['engine_net']:.2f} | ₹{r['manual_net']:.2f} | ₹{r['abs_error']:.2f} | {r['pct_error']:.2f}% | **{r['status']}** |")
        md.append(f"\n- **Mean Percentage Error**: `{mean_error:.2f}%` (Target: < 5.0%)")
        md.append(f"- **Max Percentage Error**: `{max_error:.2f}%` (Target: < 5.0%)\n")
    else:
        md.append("| ID | Origin | Commodity | Quantity (q) | Vehicle | Grade | Mandi | Manual Price (₹/q) | Manual Road (km) | Manual Net (₹/q) | Notes |")
        md.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            md.append(f"| {r['id']} | {r['origin_pincode']} | {r['commodity']} | {r['quantity_q']} | {r['vehicle']} | {r['quality_grade']} | {r['mandi_name']} | {r.get('manual_price_q') or 'TBD'} | {r.get('manual_road_km') or 'TBD'} | {r.get('manual_net_q') or 'TBD'} | {r.get('manual_notes') or ''} |")
        md.append("\n> [!NOTE]\n> Awaiting completion of manual columns in `backend/data/validation/scenarios.csv`.\n")

    md.append("## Methodology Description\n")
    md.append("The Mandi Arbitrage Advisor net profit calculation engine evaluates candidate mandis using a multi-step financial realization formula:")
    md.append("1. **Gross Price Base**: Fetches latest modal mandi prices recorded in the daily snapshot pipeline within a 3-day freshness window.")
    md.append("2. **Quality Discount**: Applies grade-specific physical auction cuts (Good 0%, Average 5%, Below Average 10%, Poor 15%).")
    md.append("3. **APMC Statutory Deductions**: Deducts local market cess and commission agent percentages from the quality-adjusted realized price.")
    md.append("4. **Freight Logistics**: Models non-linear discrete vehicle capacities using ceiling division (e.g. 10 quintals on an 8 quintal tempo requires 2 vehicles), multiplied by distance and rate per km.")
    md.append("5. **Net Realization**: Subtracts transport and optional handling charges from the net mandi realization.")
    md.append("\n## Known Sources of Error\n")
    md.append("1. **Price Timing & Snapshot Lag**: APMC physical auction rates fluctuate throughout the trading day. data.gov.in publishes single daily modal prices which may reflect a 12-24 hour delay relative to live spot bidding.")
    md.append("2. **Route Choice & Road Geometry**: Real vehicular navigation can deviate from straight-line haversine * 1.3 approximations or Google Routes API recommendations depending on rural road conditions, seasonal monsoon detours, and toll bypasses.")
    md.append("3. **Arithmetic Rounding**: Handheld calculators frequently round intermediate products (such as transport cost per quintal) to 2 decimal places, whereas the engine maintains full Python Decimal precision throughout intermediate steps and quantizes strictly at the final output boundary.")
    return "\n".join(md)

async def run_self_check():
    print("================================================================================")
    print("RUNNING FORMULA SELF-CHECK (Independent Straight-Line Decimal Implementation)")
    print("================================================================================")
    rates_cfg = load_rates_config()
    geocoder = GeocodingService()

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    all_passed = True
    print(f"{'ID':<3} | {'Commodity':<10} | {'Mandi':<20} | {'Qty':<5} | {'Engine Net':<12} | {'Indep Net':<12} | {'Diff':<8} | {'Status'}")
    print("-" * 88)

    async with async_session_factory() as db:
        for row in rows:
            sid = int(row["id"])
            pincode = row["origin_pincode"]
            commodity = row["commodity"]
            mandi_name = row["mandi_name"]
            qty = Decimal(row["quantity_q"])
            veh_name = row["vehicle"]
            grade = row["quality_grade"]

            loc = await geocoder.resolve_location(db, pincode=pincode)
            stmt = select(Mandi).where(Mandi.name == mandi_name)
            mandi = (await db.execute(stmt)).scalar_one()

            road_km = Decimal(str(round(haversine_fallback_distance_km(loc.lat, loc.lng, mandi.lat, mandi.lng, 1.3), 2)))
            prices_map, _ = await get_latest_prices_for_mandis(db, [mandi.id], commodity)
            price_q = prices_map[mandi.id].modal_price

            veh_cfg = rates_cfg.vehicles[veh_name]
            capacity_q = veh_cfg.capacity_quintals
            rate_per_km = veh_cfg.rate_per_km
            quality_cut_pct = rates_cfg.quality_grades.get(grade, Decimal("0.0"))
            fee_pct = rates_cfg.market_fee_pct_default
            comm_pct = rates_cfg.commission_pct_default

            # Engine calculation
            engine_res = calculate_net_profit(
                price_q=price_q,
                quality_cut_pct=quality_cut_pct,
                quantity_q=qty,
                vehicle_capacity_q=capacity_q,
                vehicle_rate_per_km=rate_per_km,
                market_fee_pct=fee_pct,
                commission_pct=comm_pct,
                road_km=road_km,
                include_other_charges=False,
            )

            # Independent straight-line calculation
            indep_val = independent_straight_line_net_q(
                price=price_q,
                cut_pct=quality_cut_pct,
                qty=qty,
                veh_cap=capacity_q,
                veh_rate=rate_per_km,
                fee_pct=fee_pct,
                comm_pct=comm_pct,
                road_km=road_km,
                include_other=False,
            )

            diff = abs(engine_res.net_q - indep_val)
            passed = diff <= Decimal("0.01")
            status = "PASS" if passed else "FAIL"
            if not passed:
                all_passed = False

            print(f"{sid:<3} | {commodity:<10} | {mandi_name[:20]:<20} | {str(qty):<5} | Rs.{round_currency(engine_res.net_q):<10} | Rs.{round_currency(indep_val):<10} | Rs.{diff:<6.4f} | {status}")

    print("=" * 88)
    if all_passed:
        print("[SUCCESS] All 10 scenarios passed independent straight-line self-check within 0.01 Rs.")
        return 0
    else:
        print("[FAILURE] One or more scenarios failed independent straight-line self-check.")
        return 1

async def run_accuracy_validation():
    print("================================================================================")
    print("RUNNING ACCURACY VALIDATION AGAINST GROUND TRUTH")
    print("================================================================================")
    
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Check how many rows have manual values
    filled_rows = []
    for r in rows:
        val = r.get("manual_net_q", "").strip()
        if val:
            try:
                float(val)
                filled_rows.append(r)
            except ValueError:
                pass

    if len(filled_rows) < 10:
        print(f"\n[NOTICE] {len(filled_rows)} of 10 scenarios have manual ground truth values filled.")
        print(f"Please fill all 10 manual scenario rows in: {CSV_PATH}")
        print("Detailed instructions have been written to docs/VALIDATION.md.")
        
        # Write initial template to docs/VALIDATION.md
        content = generate_validation_markdown(rows)
        DOCS_VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DOCS_VALIDATION_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {DOCS_VALIDATION_PATH} with validation instructions.\n")
        return 1

    rates_cfg = load_rates_config()
    geocoder = GeocodingService()
    results = []
    pct_errors = []

    async with async_session_factory() as db:
        for r in filled_rows:
            sid = int(r["id"])
            pincode = r["origin_pincode"]
            commodity = r["commodity"]
            mandi_name = r["mandi_name"]
            qty = Decimal(r["quantity_q"])
            veh_name = r["vehicle"]
            grade = r["quality_grade"]
            manual_net = Decimal(r["manual_net_q"])

            loc = await geocoder.resolve_location(db, pincode=pincode)
            stmt = select(Mandi).where(Mandi.name == mandi_name)
            mandi = (await db.execute(stmt)).scalar_one()

            road_km = Decimal(str(round(haversine_fallback_distance_km(loc.lat, loc.lng, mandi.lat, mandi.lng, 1.3), 2)))
            prices_map, _ = await get_latest_prices_for_mandis(db, [mandi.id], commodity)
            price_q = prices_map[mandi.id].modal_price

            veh_cfg = rates_cfg.vehicles[veh_name]
            capacity_q = veh_cfg.capacity_quintals
            rate_per_km = veh_cfg.rate_per_km
            quality_cut_pct = rates_cfg.quality_grades.get(grade, Decimal("0.0"))
            fee_pct = rates_cfg.market_fee_pct_default
            comm_pct = rates_cfg.commission_pct_default

            engine_res = calculate_net_profit(
                price_q=price_q,
                quality_cut_pct=quality_cut_pct,
                quantity_q=qty,
                vehicle_capacity_q=capacity_q,
                vehicle_rate_per_km=rate_per_km,
                market_fee_pct=fee_pct,
                commission_pct=comm_pct,
                road_km=road_km,
                include_other_charges=False,
            )

            engine_net = engine_res.net_q
            abs_err = abs(engine_net - manual_net)
            pct_err = float((abs_err / abs(manual_net)) * Decimal("100")) if manual_net != 0 else 0.0
            pct_errors.append(pct_err)
            passed = pct_err <= 5.0
            status = "PASS" if passed else "FAIL"

            results.append({
                "id": sid,
                "origin": pincode,
                "commodity": commodity,
                "qty": str(qty),
                "vehicle": veh_name,
                "grade": grade,
                "mandi": mandi_name,
                "engine_net": float(engine_net),
                "manual_net": float(manual_net),
                "abs_error": float(abs_err),
                "pct_error": pct_err,
                "status": status,
            })

    mean_err = sum(pct_errors) / len(pct_errors)
    max_err = max(pct_errors)

    print(f"{'ID':<3} | {'Commodity':<10} | {'Mandi':<20} | {'Engine Net':<12} | {'Manual Net':<12} | {'Abs Error':<10} | {'% Error':<8} | {'Status'}")
    print("-" * 92)
    for res in results:
        print(f"{res['id']:<3} | {res['commodity']:<10} | {res['mandi'][:20]:<20} | Rs.{res['engine_net']:<10.2f} | Rs.{res['manual_net']:<10.2f} | Rs.{res['abs_error']:<8.2f} | {res['pct_error']:<6.2f}% | {res['status']}")
    print("-" * 92)
    print(f"Mean % Error: {mean_err:.2f}% | Max % Error: {max_err:.2f}%")
    print("=" * 92)

    content = generate_validation_markdown(rows, results=results, mean_error=mean_err, max_error=max_err)
    with open(DOCS_VALIDATION_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated validation report in {DOCS_VALIDATION_PATH}")

    all_pass = all(r["status"] == "PASS" for r in results)
    return 0 if all_pass else 1

def main():
    parser = argparse.ArgumentParser(description="Mandi Arbitrage Accuracy Validation")
    parser.add_argument("--self-check", action="store_true", help="Run independent straight-line formula self-check")
    args = parser.parse_args()

    if args.self_check:
        code = asyncio.run(run_self_check())
        sys.exit(code)
    else:
        code = asyncio.run(run_accuracy_validation())
        sys.exit(code)

if __name__ == "__main__":
    main()
