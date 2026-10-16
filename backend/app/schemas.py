from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
import re

# Standard error response format: { error: {code, message, details?} }
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail

# Health response
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.01.00"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Meta responses
class CropSchema(BaseModel):
    id: str
    name_en: str
    name_hi: str
    aliases: List[str]

class CropsResponse(BaseModel):
    crops: List[CropSchema]

class VehicleSchema(BaseModel):
    id: str
    name: str
    capacity_quintals: Decimal
    rate_per_km: Decimal

class VehiclesResponse(BaseModel):
    vehicles: Dict[str, VehicleSchema]

class RatesResponse(BaseModel):
    status: str
    note: str
    market_fee_pct_default: Decimal
    commission_pct_default: Decimal
    state_overrides: Dict[str, Any]
    vehicles: Dict[str, Any]
    quality_grades: Dict[str, Decimal]
    custom_quality_cut_pct_range: Dict[str, Decimal]
    other_charges_per_quintal: Dict[str, Decimal]
    fallback_distance: Dict[str, Decimal]
    defaults: Dict[str, Any]

class StatesResponse(BaseModel):
    states: List[str]

class DistrictsResponse(BaseModel):
    state: str
    districts: List[str]

# Compare Request & Response Schemas
class QualityInput(BaseModel):
    grade: Optional[str] = None
    custom_pct: Optional[Decimal] = None

class OverridesInput(BaseModel):
    market_fee_pct: Optional[Decimal] = None
    commission_pct: Optional[Decimal] = None
    rate_per_km: Optional[Decimal] = None

class CompareRequest(BaseModel):
    pincode: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    commodity: str
    variety: Optional[str] = None
    quantity_quintals: Decimal = Field(default=Decimal("10.0"), gt=0)
    vehicle: str = "pickup"
    quality: QualityInput = Field(default_factory=lambda: QualityInput(grade="Good"))
    price_basis: Literal["modal", "min", "max"] = "modal"
    overrides: Optional[OverridesInput] = None
    include_other_charges: bool = False
    limit: int = Field(default=5, ge=1, le=10)

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^[1-9][0-9]{5}$", v):
            raise ValueError("Pincode must be a 6-digit number not starting with 0 (^[1-9][0-9]{5}$)")
        return v

class ResolvedLocation(BaseModel):
    lat: float
    lng: float
    label: str
    source: str

class MandiBrief(BaseModel):
    id: int
    name: str
    district: str
    state: str
    lat: float
    lng: float

class PriceBrief(BaseModel):
    basis: str
    value: Decimal
    min: Optional[Decimal] = None
    max: Optional[Decimal] = None
    arrival_date: date
    age_days: int
    variety: str
    varieties_used: int
    is_stale: bool

class DistanceBrief(BaseModel):
    road_km: float
    duration_min: float
    source: str

class BreakdownBrief(BaseModel):
    price_q: Decimal
    quality_cut_q: Decimal
    realized_q: Decimal
    mandi_fee_q: Decimal
    transport_q: Decimal
    other_q: Decimal
    net_q: Decimal
    net_total: Decimal

class VsNearestBrief(BaseModel):
    delta_q: Decimal
    delta_total: Decimal

class CompareResultItem(BaseModel):
    rank: int
    is_nearest: bool
    mandi: MandiBrief
    price: PriceBrief
    distance: DistanceBrief
    breakdown: BreakdownBrief
    vs_nearest: VsNearestBrief

class SummaryBrief(BaseModel):
    best_mandi_id: int
    nearest_mandi_id: int
    extra_profit_q: Decimal
    extra_profit_total: Decimal

class AssumptionsBrief(BaseModel):
    rates_status: str
    market_fee_pct: Decimal
    commission_pct: Decimal
    vehicle: str
    rate_per_km: Decimal
    quality_cut_pct: Decimal
    round_trip_factor: Decimal

class WarningItem(BaseModel):
    code: Literal[
        "STALE_PRICE",
        "DISTANCE_FALLBACK",
        "GEOCODE_FALLBACK",
        "FEWER_THAN_LIMIT",
        "NO_PRICE_DATA",
        "ASSUMED_RATES",
    ]
    message: str

class CacheStatus(BaseModel):
    geocode: str
    distance: str
    prices: str

class CompareMeta(BaseModel):
    elapsed_ms: float
    cache: CacheStatus
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompareResponse(BaseModel):
    query: Dict[str, Any]
    results: List[CompareResultItem]
    summary: SummaryBrief
    assumptions: AssumptionsBrief
    warnings: List[WarningItem]
    meta: CompareMeta

# Trend Response Schemas
class TrendPoint(BaseModel):
    date: date
    modal: Optional[Decimal] = None
    min: Optional[Decimal] = None
    max: Optional[Decimal] = None
    is_seeded: bool = False

class TrendSeries(BaseModel):
    mandi_id: int
    mandi_name: str
    points: List[TrendPoint]

class TrendResponse(BaseModel):
    series: List[TrendSeries]

# Admin Ingest Response
class IngestResponse(BaseModel):
    status: str
    records_fetched: int
    records_inserted: int
    duration_seconds: float
