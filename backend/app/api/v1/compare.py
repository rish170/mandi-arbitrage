from fastapi import APIRouter, HTTPException
from app.schemas import CompareRequest, CompareResponse

router = APIRouter(tags=["Compare"])

@router.post("/compare", response_model=CompareResponse)
async def compare_mandis(request: CompareRequest) -> CompareResponse:
    raise HTTPException(
        status_code=501,
        detail={
            "code": "NOT_IMPLEMENTED",
            "message": "Compare endpoint is scheduled for Phase 4",
        },
    )
