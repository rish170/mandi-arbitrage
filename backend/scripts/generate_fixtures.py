import asyncio
import csv
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select

from app.config_loader import load_rates_config
from app.core.geo import haversine_fallback_distance_km
from app.core.profit import calculate_net_profit, round_currency
from app.db import async_session_factory
from app.models import Mandi
from app.services.geocode import GeocodingService
from app.services.prices import get_latest_prices_for_mandis

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "validation" / "scenarios.csv"
FIXTURE_PATH = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "validation_snapshot.json"

async def main():
    rates_cfg = load_rates_config()
    geocoder = GeocodingService()
    
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    snapshots = []
    async with async_session_factory() as db:
        for row in reader:
            sid = int(row["id"])
            pincode = row["origin_pincode"]
            commodity = row["commodity"]
            mandi_name = row["mandi_name"]
            qty = Decimal(row["quantity_q"])
            veh_name = row["vehicle"]
            grade = row["quality_grade"]

            # Geocode
            loc = await geocoder.resolve_location(db, pincode=pincode)

            # Mandi
            stmt = select(Mandi).where(Mandi.name == mandi_name)
            mandi = (await db.execute(stmt)).scalar_one()

            # Road distance (haversine * 1.3 fallback estimate)
            road_km = Decimal(str(round(haversine_fallback_distance_km(loc.lat, loc.lng, mandi.lat, mandi.lng, 1.3), 2)))

            # Price
            prices_map, _ = await get_latest_prices_for_mandis(db, [mandi.id], commodity)
            price_q = prices_map[mandi.id].modal_price

            # Vehicle
            veh_cfg = rates_cfg.vehicles[veh_name]
            capacity_q = veh_cfg.capacity_quintals
            rate_per_km = veh_cfg.rate_per_km

            # Quality cut
            quality_cut_pct = rates_cfg.quality_grades.get(grade, Decimal("0.0"))

            # Fee and commission (Maharashtra default)
            market_fee_pct = rates_cfg.market_fee_pct_default
            commission_pct = rates_cfg.commission_pct_default

            # Hand calculation arithmetic:
            # 1. Quality cut
            quality_cut_q = price_q * (quality_cut_pct / Decimal("100"))
            realized_q = price_q - quality_cut_q

            # 2. Statutory mandi fee + commission
            fee_cut_q = realized_q * ((market_fee_pct + commission_pct) / Decimal("100"))

            # 3. Vehicles needed (ceil division)
            div_val = qty / capacity_q
            vehicles_needed = math.ceil(float(div_val))
            transport_total = Decimal(vehicles_needed) * rate_per_km * road_km * Decimal("1.0")
            transport_q = transport_total / qty

            # 4. Other charges = 0.0
            other_q = Decimal("0.0")

            # 5. Net realization
            net_q = realized_q - fee_cut_q - transport_q - other_q
            net_total = net_q * qty

            # Verify with engine
            engine_res = calculate_net_profit(
                price_q=price_q,
                quality_cut_pct=quality_cut_pct,
                quantity_q=qty,
                vehicle_capacity_q=capacity_q,
                vehicle_rate_per_km=rate_per_km,
                market_fee_pct=market_fee_pct,
                commission_pct=commission_pct,
                road_km=road_km,
                include_other_charges=False,
            )

            assert abs(engine_res.net_q - net_q) < Decimal("0.0001")

            snapshots.append({
                "id": sid,
                "origin_pincode": pincode,
                "commodity": commodity,
                "mandi_id": mandi.id,
                "mandi_name": mandi_name,
                "quantity_q": str(qty),
                "vehicle": veh_name,
                "vehicle_capacity_q": str(capacity_q),
                "vehicle_rate_per_km": str(rate_per_km),
                "quality_grade": grade,
                "quality_cut_pct": str(quality_cut_pct),
                "market_fee_pct": str(market_fee_pct),
                "commission_pct": str(commission_pct),
                "road_km": str(road_km),
                "price_q": str(price_q),
                "quality_cut_q": str(round_currency(quality_cut_q)),
                "realized_q": str(round_currency(realized_q)),
                "mandi_fee_q": str(round_currency(fee_cut_q)),
                "vehicles_needed": vehicles_needed,
                "transport_total": str(round_currency(transport_total)),
                "transport_q": str(round_currency(transport_q)),
                "net_q": str(round_currency(net_q)),
                "net_total": str(round_currency(net_total)),
            })

    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FIXTURE_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshots, f, indent=2)

    print(f"Generated {len(snapshots)} frozen scenario snapshots at {FIXTURE_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
