from fastapi import APIRouter, Header, HTTPException
from app.schemas import IngestResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/ingest", response_model=IngestResponse)
async def trigger_ingest(
    x_admin_token: str = Header(..., alias="X-Admin-Token")
) -> IngestResponse:
    raise HTTPException(
        status_code=501,
        detail={
            "code": "NOT_IMPLEMENTED",
            "message": "Admin ingestion endpoint is scheduled for Phase 3",
        },
    )
