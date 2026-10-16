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

@router.get("/crops", response_model=CropsResponse)
async def get_crops() -> CropsResponse:
    crops_cfg = load_crops_config()
    crops_list = [CropSchema.model_validate(c.model_dump()) for c in crops_cfg.crops]
    return CropsResponse(crops=crops_list)

@router.get("/vehicles", response_model=VehiclesResponse)
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

@router.get("/rates", response_model=RatesResponse)
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

@router.get("/states", response_model=StatesResponse)
async def get_states(db: AsyncSession = Depends(get_db)) -> StatesResponse:
    result = await db.execute(select(Mandi.state).distinct().order_by(Mandi.state))
    states = [row[0] for row in result.all()]
    if not states:
        states = ["Maharashtra"]
    return StatesResponse(states=states)

@router.get("/districts", response_model=DistrictsResponse)
async def get_districts(
    state: str = Query(..., description="State name to get districts for"),
    db: AsyncSession = Depends(get_db),
) -> DistrictsResponse:
    result = await db.execute(
        select(Mandi.district)
        .where(Mandi.state == state)
        .distinct()
        .order_by(Mandi.district)
    )
    districts = [row[0] for row in result.all()]
    return DistrictsResponse(state=state, districts=districts)
