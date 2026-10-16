from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config_loader import load_crops_config, load_rates_config
from app.db import get_db
from app.models import Mandi
from app.schemas import (
    CropSchema,
    CropsResponse,
    DistrictsResponse,
    RatesResponse,
    StatesResponse,
    VehicleSchema,
    VehiclesResponse,
)

router = APIRouter(prefix="/meta", tags=["Metadata"])

@router.get("/crops", response_model=CropsResponse, summary="List supported crops", description="Returns canonical list of supported crops with English and Hindi names and query aliases.")
async def get_crops() -> CropsResponse:
    crops_cfg = load_crops_config()
    crops_list = [CropSchema.model_validate(c.model_dump()) for c in crops_cfg.crops]
    return CropsResponse(crops=crops_list)

@router.get("/vehicles", response_model=VehiclesResponse, summary="List vehicle specifications", description="Returns standard freight vehicles with capacities in quintals and default per-km rates.")
async def get_vehicles() -> VehiclesResponse:
    rates_cfg = load_rates_config()
    vehicles_dict = {
        vid: VehicleSchema(
            id=vid,
            name=v.name,
            capacity_quintals=v.capacity_quintals,
            rate_per_km=v.rate_per_km,
        )
        for vid, v in rates_cfg.vehicles.items()
    }
    return VehiclesResponse(vehicles=vehicles_dict)

@router.get("/rates", response_model=RatesResponse, summary="Get rate card and assumptions", description="Returns statutory fee defaults, state overrides, vehicle rates, quality cuts, and assumption status flags.")
async def get_rates() -> RatesResponse:
    rates_cfg = load_rates_config()
    return RatesResponse(
        status=rates_cfg.status,
        note=rates_cfg.note,
        market_fee_pct_default=rates_cfg.market_fee_pct_default,
        commission_pct_default=rates_cfg.commission_pct_default,
        state_overrides=rates_cfg.state_overrides,
        vehicles=rates_cfg.vehicles,
        quality_grades=rates_cfg.quality_grades,
        custom_quality_cut_pct_range=rates_cfg.custom_quality_cut_pct_range,
        other_charges_per_quintal=rates_cfg.other_charges_per_quintal,
        fallback_distance=rates_cfg.fallback_distance,
        defaults=rates_cfg.defaults,
    )

from cachetools import TTLCache

META_CACHE = TTLCache(maxsize=100, ttl=3600)

@router.get("/states", response_model=StatesResponse, summary="List active states", description="Returns distinct states containing active mandis in the database (cached 1h).")
async def get_states(db: AsyncSession = Depends(get_db)) -> StatesResponse:
    cache_key = "meta:states"
    if cache_key in META_CACHE:
        return StatesResponse(states=META_CACHE[cache_key])

    result = await db.execute(select(Mandi.state).distinct().order_by(Mandi.state))
    states = [row[0] for row in result.all()]
    if not states:
        states = ["Maharashtra"]
    META_CACHE[cache_key] = states
    return StatesResponse(states=states)

@router.get("/districts", response_model=DistrictsResponse, summary="List districts for a state", description="Returns distinct districts with active mandis for the requested state (cached 1h).")
async def get_districts(
    state: str = Query(..., description="State name to get districts for"),
    db: AsyncSession = Depends(get_db),
) -> DistrictsResponse:
    cache_key = f"meta:districts:{state.lower()}"
    if cache_key in META_CACHE:
        return DistrictsResponse(state=state, districts=META_CACHE[cache_key])

    result = await db.execute(
        select(Mandi.district)
        .where(Mandi.state == state)
        .distinct()
        .order_by(Mandi.district)
    )
    districts = [row[0] for row in result.all()]
    META_CACHE[cache_key] = districts
    return DistrictsResponse(state=state, districts=districts)
