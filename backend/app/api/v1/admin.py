from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.schemas import IngestResponse
from app.services.ingest import ingest_prices_for_crops

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/ingest", response_model=IngestResponse)
async def trigger_ingest(
    x_admin_token: str = Header(..., alias="X-Admin-Token"),
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    if x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Invalid or missing admin token",
            },
        )

    res = await ingest_prices_for_crops(db=db)
    return IngestResponse(
        status="success",
        records_fetched=res.total_fetched,
        records_inserted=res.inserted,
        duration_seconds=res.duration_seconds,
    )
