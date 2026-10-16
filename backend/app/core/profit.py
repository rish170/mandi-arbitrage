from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
import math
from typing import Optional

TWO_PLACES = Decimal("0.01")

def round_currency(val: Decimal) -> Decimal:
    """Round a Decimal value to 2 decimal places using standard half-up rounding."""
    return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

@dataclass(frozen=True)
class ProfitBreakdown:
    """
    Detailed breakdown of net profit calculation per quintal and in total.
    All monetary and quantity figures are pure Decimals.
    """
    price_q: Decimal
    quality_cut_q: Decimal
    realized_q: Decimal
    mandi_fee_q: Decimal
    transport_q: Decimal
    other_q: Decimal
    net_q: Decimal
    net_total: Decimal
    vehicles_needed: int
    transport_total: Decimal

    def to_rounded_dict(self) -> dict:
        """Serialize breakdown with currency values rounded to 2 decimal places."""
        return {
            "price_q": round_currency(self.price_q),
            "quality_cut_q": round_currency(self.quality_cut_q),
            "realized_q": round_currency(self.realized_q),
            "mandi_fee_q": round_currency(self.mandi_fee_q),
            "transport_q": round_currency(self.transport_q),
            "other_q": round_currency(self.other_q),
            "net_q": round_currency(self.net_q),
            "net_total": round_currency(self.net_total),
        }

def calculate_net_profit(
    price_q: Optional[Decimal],
    quality_cut_pct: Decimal,
    quantity_q: Decimal,
    vehicle_capacity_q: Decimal,
    vehicle_rate_per_km: Decimal,
    market_fee_pct: Decimal,
    commission_pct: Decimal,
    road_km: Decimal,
    round_trip_factor: Decimal = Decimal("1.0"),
    include_other_charges: bool = False,
    loading_unloading_q: Decimal = Decimal("3.0"),
    weighing_q: Decimal = Decimal("1.0"),
) -> ProfitBreakdown:
    """
    Calculate the net profit per quintal and total net profit according to the official formula:

        quality_cut_q      = price_q * quality_cut_pct / 100
        realized_q         = price_q - quality_cut_q
        mandi_fee_q        = realized_q * (market_fee_pct + commission_pct) / 100
        vehicles_needed    = ceil(quantity_q / vehicle_capacity_q)
        transport_total    = vehicles_needed * vehicle_rate_per_km * road_km * round_trip_factor
        transport_q        = transport_total / quantity_q
        other_q            = (loading_unloading_q + weighing_q) if include_other_charges else 0
        net_q              = realized_q - mandi_fee_q - transport_q - other_q
        net_total          = net_q * quantity_q

    All inputs and calculations use arbitrary-precision Python Decimal.
    """
    if price_q is None:
        raise ValueError("Mandi price cannot be None or missing.")
    if quantity_q <= Decimal("0"):
        raise ValueError("Quantity must be greater than 0 quintals.")
    if vehicle_capacity_q <= Decimal("0"):
        raise ValueError("Vehicle capacity must be greater than 0 quintals.")
    if vehicle_rate_per_km < Decimal("0"):
        raise ValueError("Vehicle rate per km cannot be negative.")
    if road_km < Decimal("0"):
        raise ValueError("Road distance cannot be negative.")
    if price_q < Decimal("0"):
        raise ValueError("Mandi price cannot be negative.")

    # 1. Quality deduction
    quality_cut_q = price_q * (quality_cut_pct / Decimal("100"))
    realized_q = price_q - quality_cut_q

    # 2. Statutory APMC market fee and commission agent fee
    combined_fee_pct = market_fee_pct + commission_pct
    mandi_fee_q = realized_q * (combined_fee_pct / Decimal("100"))

    # 3. Transport calculations
    # vehicles_needed = ceil(quantity_q / vehicle_capacity_q)
    div_val = quantity_q / vehicle_capacity_q
    vehicles_needed = int(div_val.quantize(Decimal("1"), rounding=ROUND_CEILING))
    if vehicles_needed == 0:
        vehicles_needed = 1

    transport_total = (
        Decimal(vehicles_needed)
        * vehicle_rate_per_km
        * road_km
        * round_trip_factor
    )
    transport_q = transport_total / quantity_q

    # 4. Miscellaneous mandi charges
    if include_other_charges:
        other_q = loading_unloading_q + weighing_q
    else:
        other_q = Decimal("0")

    # 5. Final net realization
    net_q = realized_q - mandi_fee_q - transport_q - other_q
    net_total = net_q * quantity_q

    return ProfitBreakdown(
        price_q=price_q,
        quality_cut_q=quality_cut_q,
        realized_q=realized_q,
        mandi_fee_q=mandi_fee_q,
        transport_q=transport_q,
        other_q=other_q,
        net_q=net_q,
        net_total=net_total,
        vehicles_needed=vehicles_needed,
        transport_total=transport_total,
    )
