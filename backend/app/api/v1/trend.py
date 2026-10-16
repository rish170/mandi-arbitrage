from fastapi import APIRouter, HTTPException, Query
from app.schemas import TrendResponse

router = APIRouter(tags=["Trend"])

@router.get("/trend", response_model=TrendResponse)
async def get_price_trend(
    mandi_ids: str = Query(..., description="Comma-separated mandi IDs, e.g. 1,2,3"),
    commodity: str = Query(..., description="Commodity name"),
    days: int = Query(7, description="Number of historical days"),
) -> TrendResponse:
    raise HTTPException(
        status_code=501,
        detail={
            "code": "NOT_IMPLEMENTED",
            "message": "Trend endpoint is scheduled for Phase 4",
        },
    )
