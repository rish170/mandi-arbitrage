from decimal import Decimal
import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

CONFIG_DIR = Path(__file__).resolve().parent / "config"

class VehicleConfig(BaseModel):
    name: str
    capacity_quintals: Decimal
    rate_per_km: Decimal

class StateRateOverride(BaseModel):
    market_fee_pct: Optional[Decimal] = None
    commission_pct: Optional[Decimal] = None

class RatesConfig(BaseModel):
    status: str
    note: str
    market_fee_pct_default: Decimal
    commission_pct_default: Decimal
    state_overrides: Dict[str, StateRateOverride] = Field(default_factory=dict)
    vehicles: Dict[str, VehicleConfig]
    quality_grades: Dict[str, Decimal]
    custom_quality_cut_pct_range: Dict[str, Decimal]
    other_charges_per_quintal: Dict[str, Decimal]
    fallback_distance: Dict[str, Decimal]
    defaults: Dict[str, object]

class CropItem(BaseModel):
    id: str
    name_en: str
    name_hi: str
    aliases: List[str]

class CropsConfig(BaseModel):
    crops: List[CropItem]

def load_rates_config(filepath: Optional[Path] = None) -> RatesConfig:
    path = filepath or (CONFIG_DIR / "rates.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return RatesConfig.model_validate(data)

def load_crops_config(filepath: Optional[Path] = None) -> CropsConfig:
    path = filepath or (CONFIG_DIR / "crops.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CropsConfig.model_validate(data)
