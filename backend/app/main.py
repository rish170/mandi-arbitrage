from datetime import datetime, timezone
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import admin, compare, meta, trend
from app.config import settings
from app.schemas import ErrorDetail, ErrorResponse, HealthResponse

from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter

app = FastAPI(
    title="Mandi Arbitrage Advisor API",
    description="Backend API for mandi price arbitrage comparison, net profit calculations, and historical trends.",
    version="0.01.00",
)
app.state.limiter = limiter

# CORS middleware
origins = [settings.FRONTEND_ORIGIN]
if settings.ENV != "production":
    origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Process time middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time-ms"] = f"{elapsed_ms:.2f}"
    return response

# Standard error exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": jsonable_encoder(exc.errors()),
            }
        },
    )

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit exceeded: {exc.detail}",
                "details": None,
            }
        },
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict):
        code = exc.detail.get("code", f"HTTP_{exc.status_code}")
        message = exc.detail.get("message", str(exc.detail))
        details = exc.detail.get("details", None)
    else:
        code = f"HTTP_{exc.status_code}"
        message = str(exc.detail)
        details = None

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
            }
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": str(exc) if settings.ENV != "production" else "Internal server error",
                "details": None,
            }
        },
    )

# Direct /health endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def root_health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="0.01.00", timestamp=datetime.now(timezone.utc))

# API v1 routes
app.include_router(meta.router, prefix="/api/v1")
app.include_router(compare.router, prefix="/api/v1")
app.include_router(trend.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def v1_health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="0.01.00", timestamp=datetime.now(timezone.utc))
