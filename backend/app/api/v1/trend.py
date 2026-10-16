from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Mandi
from app.schemas import TrendResponse, TrendSeries
from app.services.prices import get_trend_for_mandis

router = APIRouter(tags=["Trend"])

@router.get("/trend", response_model=TrendResponse)
async def get_price_trend(
    mandi_ids: str = Query(..., description="Comma-separated mandi IDs, e.g. 1,2,3"),
    commodity: str = Query(..., description="Commodity canonical name, e.g. Wheat"),
    days: int = Query(7, ge=1, le=30, description="Number of historical days (default: 7)"),
    db: AsyncSession = Depends(get_db),
) -> TrendResponse:
    try:
        id_list = [int(i.strip()) for i in mandi_ids.split(",") if i.strip()]
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_MANDI_IDS",
                "message": "mandi_ids must be a comma-separated list of integers.",
            },
        )

    if not id_list:
        return TrendResponse(series=[])

    # Fetch mandi names for the requested IDs
    stmt = select(Mandi.id, Mandi.name).where(Mandi.id.in_(id_list))
    rows = (await db.execute(stmt)).all()
    mandi_names = {row[0]: row[1] for row in rows}

    series_data = await get_trend_for_mandis(
        db=db,
        mandi_ids=id_list,
        mandi_names=mandi_names,
        commodity=commodity,
        days=days,
    )

    return TrendResponse(series=series_data)
