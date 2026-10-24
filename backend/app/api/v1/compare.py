import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.config_loader import load_crops_config, load_rates_config
from app.core.profit import calculate_net_profit, round_currency
from app.core.ranking import MandiComparisonItem, rank_and_summarize
from app.db import async_session_factory, get_db
from app.models import Mandi
from app.schemas import (
    AssumptionsBrief,
    CacheStatus,
    CompareMeta,
    CompareRequest,
    CompareResponse,
    CompareResultItem,
    ResolvedLocation,
    SummaryBrief,
    WarningItem,
)
from app.services.distance import DistanceService
from app.services.geocode import GeocodingService
from app.services.mandis import get_candidate_mandis
from app.services.prices import get_latest_prices_for_mandis

logger = logging.getLogger(__name__)

from app.core.limiter import limiter

router = APIRouter(tags=["Compare"])

geocoder_service = GeocodingService()
distance_service = DistanceService()

def find_canonical_crop(commodity_query: str) -> Optional[str]:
    """Match requested commodity to canonical English crop name from crops.json."""
    crops_cfg = load_crops_config()
    q_low = commodity_query.strip().lower()
    for crop in crops_cfg.crops:
        if crop.name_en.lower() == q_low or crop.name_hi.lower() == q_low:
            return crop.name_en
        for alias in crop.aliases:
            if alias.lower() == q_low:
                return crop.name_en
    return None

@router.post(
    "/compare",
    response_model=CompareResponse,
    summary="Compare mandis by net profit",
    description="Resolves origin location, finds candidate mandis within radius with active prices, computes batched road distances, calculates net profit per quintal deducting freight, market fees, and quality cuts, ranks mandis descending by net realization, and returns a detailed comparison breakdown.",
    responses={
        200: {"description": "Successful comparison with ranked mandi results, summary, assumptions, and warnings."},
        422: {"description": "Validation error (invalid pincode, unknown commodity, or missing location)."},
        429: {"description": "Rate limit exceeded (30 requests per minute per IP address)."},
    },
)
@limiter.limit("30/minute")
async def compare_mandis(
    request: Request,
    body: CompareRequest,
    db: AsyncSession = Depends(get_db),
) -> CompareResponse:
    start_time = time.perf_counter()
    warnings: List[WarningItem] = []
    warning_codes: set[str] = set()

    def add_warning(code: str, message: str):
        if code not in warning_codes:
            warning_codes.add(code)
            warnings.append(WarningItem(code=code, message=message))

    # Always add ASSUMED_RATES warning as rates carry unverified assumption status
    add_warning(
        "ASSUMED_RATES",
        "Statutory market fees and freight rates are unverified estimates (status: ASSUMPTION_UNVERIFIED).",
    )

    # 1. Validate location inputs
    if not body.pincode and not (body.state and body.district):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "MISSING_LOCATION",
                "message": "Either a 6-digit pincode or state and district must be provided.",
            },
        )

    # 2. Validate crop
    canonical_crop = find_canonical_crop(body.commodity)
    if not canonical_crop:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "UNKNOWN_COMMODITY",
                "message": f"Commodity '{body.commodity}' is not supported. Supported crops: Wheat, Rice (Paddy), Soyabean, Cotton, Onion, Potato, Tomato.",
            },
        )

    # 3. Resolve user location
    loc_res = await geocoder_service.resolve_location(
        db, pincode=body.pincode, state=body.state, district=body.district
    )
    if loc_res.source == "nominatim":
        add_warning(
            "GEOCODE_FALLBACK",
            "Coordinates were resolved using OpenStreetMap Nominatim fallback.",
        )

    origin_key = body.pincode if body.pincode else f"{body.state}:{body.district}".lower()
    resolved_loc = ResolvedLocation(
        lat=loc_res.lat,
        lng=loc_res.lng,
        label=loc_res.label,
        source=loc_res.source,
    )

    # 4. Find candidate mandis within MAX_RADIUS_KM
    candidates_raw = await get_candidate_mandis(
        db=db,
        origin_lat=loc_res.lat,
        origin_lng=loc_res.lng,
        commodity=canonical_crop,
        max_radius_km=float(settings.MAX_RADIUS_KM),
        max_age_days=settings.PRICE_MAX_AGE_DAYS,
        limit=10,  # Top 10 by haversine for distance routing
    )

    if not candidates_raw:
        # Check if there are any mandis in radius regardless of price
        stmt_any = select(func.count(Mandi.id)).where(Mandi.lat != 0.0)
        total_mandis = (await db.execute(stmt_any)).scalar_one()
        if total_mandis > 0:
            add_warning(
                "NO_PRICE_DATA",
                f"No mandis within {settings.MAX_RADIUS_KM} km have active prices for {canonical_crop} within the last {settings.PRICE_MAX_AGE_DAYS} days.",
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return CompareResponse(
            query=body.model_dump(),
            results=[],
            summary=SummaryBrief(
                best_mandi_id=0,
                nearest_mandi_id=0,
                extra_profit_q=Decimal("0.00"),
                extra_profit_total=Decimal("0.00"),
            ),
            assumptions=AssumptionsBrief(
                rates_status="ASSUMPTION_UNVERIFIED",
                market_fee_pct=Decimal("1.0"),
                commission_pct=Decimal("2.0"),
                vehicle=body.vehicle,
                rate_per_km=Decimal("18.0"),
                quality_cut_pct=Decimal("0.0"),
                round_trip_factor=Decimal("1.0"),
            ),
            warnings=warnings,
            meta=CompareMeta(
                elapsed_ms=round(elapsed_ms, 2),
                cache=CacheStatus(
                    geocode="hit" if loc_res.cache_hit else "miss",
                    distance="miss",
                    prices="miss",
                ),
                generated_at=datetime.now(timezone.utc),
            ),
        )

    # 5. Concurrently calculate batched road distances and fetch detailed aggregated prices
    destinations = [(m.id, m.lat, m.lng) for m, _, _ in candidates_raw]
    candidate_mandi_ids = [m.id for m, _, _ in candidates_raw]

    async with async_session_factory() as dist_db:
        (
            (distance_map, has_distance_fallback),
            (prices_map, price_cache_hit),
        ) = await asyncio.gather(
            distance_service.get_distances(
                db=dist_db,
                origin_lat=loc_res.lat,
                origin_lng=loc_res.lng,
                origin_key=origin_key,
                destinations=destinations,
            ),
            get_latest_prices_for_mandis(
                db=db,
                mandi_ids=candidate_mandi_ids,
                commodity=canonical_crop,
                variety=body.variety,
                max_age_days=settings.PRICE_MAX_AGE_DAYS,
            ),
        )

    if has_distance_fallback:
        add_warning(
            "DISTANCE_FALLBACK",
            "Road distance calculated using haversine * 1.3 fallback estimate.",
        )

    # 7. Re-rank by road_km ascending and select up to body.limit (default 5)
    candidates_with_dist = []
    for m, _, _ in candidates_raw:
        dist_info = distance_map.get(m.id)
        price_info = prices_map.get(m.id)
        if dist_info and price_info:
            candidates_with_dist.append((m, dist_info, price_info))

    candidates_with_dist.sort(key=lambda x: x[1].road_km)
    selected_candidates = candidates_with_dist[: body.limit]

    if len(selected_candidates) < body.limit:
        add_warning(
            "FEWER_THAN_LIMIT",
            f"Found {len(selected_candidates)} mandis within {settings.MAX_RADIUS_KM} km with price data (requested {body.limit}).",
        )

    # 8. Load rates and resolve overrides
    rates_cfg = load_rates_config()

    # Vehicle resolution
    veh_key = body.vehicle.lower()
    veh_cfg = rates_cfg.vehicles.get(veh_key) or rates_cfg.vehicles.get("pickup")
    capacity_q = veh_cfg.capacity_quintals
    rate_per_km = veh_cfg.rate_per_km
    if body.overrides and body.overrides.rate_per_km is not None:
        rate_per_km = body.overrides.rate_per_km

    # Fee and commission resolution
    default_state = selected_candidates[0][0].state if selected_candidates else "Maharashtra"
    state_override = rates_cfg.state_overrides.get(default_state)
    market_fee_pct = (
        state_override.market_fee_pct
        if state_override and state_override.market_fee_pct is not None
        else rates_cfg.market_fee_pct_default
    )
    commission_pct = (
        state_override.commission_pct
        if state_override and state_override.commission_pct is not None
        else rates_cfg.commission_pct_default
    )

    if body.overrides:
        if body.overrides.market_fee_pct is not None:
            market_fee_pct = body.overrides.market_fee_pct
        if body.overrides.commission_pct is not None:
            commission_pct = body.overrides.commission_pct

    # Quality cut resolution
    if body.quality.custom_pct is not None:
        quality_cut_pct = max(Decimal("0.0"), min(Decimal("30.0"), body.quality.custom_pct))
    else:
        grade_key = body.quality.grade or "Good"
        quality_cut_pct = rates_cfg.quality_grades.get(grade_key, Decimal("0.0"))

    # Other charges
    loading_unloading_q = rates_cfg.other_charges_per_quintal.get("loading_unloading", Decimal("3.0"))
    weighing_q = rates_cfg.other_charges_per_quintal.get("weighing", Decimal("1.0"))

    # 9. Compute Profit Breakdown per candidate
    comparison_items: List[MandiComparisonItem] = []
    has_stale_price = False

    for mandi, dist_info, price_info in selected_candidates:
        if price_info.is_stale:
            has_stale_price = True

        # Determine price value based on price_basis
        if body.price_basis == "min" and price_info.min_price is not None:
            price_val = price_info.min_price
        elif body.price_basis == "max" and price_info.max_price is not None:
            price_val = price_info.max_price
        else:
            price_val = price_info.modal_price

        breakdown = calculate_net_profit(
            price_q=price_val,
            quality_cut_pct=quality_cut_pct,
            quantity_q=body.quantity_quintals,
            vehicle_capacity_q=capacity_q,
            vehicle_rate_per_km=rate_per_km,
            market_fee_pct=market_fee_pct,
            commission_pct=commission_pct,
            road_km=Decimal(str(dist_info.road_km)),
            round_trip_factor=Decimal("1.0"),
            include_other_charges=body.include_other_charges,
            loading_unloading_q=loading_unloading_q,
            weighing_q=weighing_q,
        )

        comparison_items.append(
            MandiComparisonItem(
                mandi_id=mandi.id,
                name=mandi.name,
                district=mandi.district,
                state=mandi.state,
                lat=mandi.lat,
                lng=mandi.lng,
                road_km=dist_info.road_km,
                duration_min=dist_info.duration_min,
                distance_source=dist_info.source,
                price_basis=body.price_basis,
                price_val=price_val,
                min_price=price_info.min_price,
                max_price=price_info.max_price,
                arrival_date=price_info.arrival_date,
                age_days=price_info.age_days,
                variety=price_info.variety,
                varieties_used=price_info.varieties_used,
                is_stale=price_info.is_stale,
                breakdown=breakdown,
            )
        )

    if has_stale_price:
        max_age = max((p.age_days for _, _, p in selected_candidates), default=0)
        msg = (
            f"Using latest recorded prices ({max_age} days old) as real-time APMC updates are currently delayed."
            if max_age > 3
            else "One or more mandis report price data that is 2 to 3 days old."
        )
        add_warning("STALE_PRICE", msg)

    # 10. Rank and summarize
    ranked_results, summary_info = rank_and_summarize(
        comparison_items, quantity_q=body.quantity_quintals
    )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # Build response results
    res_items = [
        CompareResultItem(
            rank=r.rank,
            is_nearest=r.is_nearest,
            mandi=r.mandi,
            price=r.price,
            distance=r.distance,
            breakdown=r.breakdown,
            vs_nearest=r.vs_nearest,
        )
        for r in ranked_results
    ]

    all_dists_cached = all(d.cache_hit for d in distance_map.values())
    dist_cache_status = "hit" if all_dists_cached else "miss"

    return CompareResponse(
        query={
            **body.model_dump(),
            "resolved_location": resolved_loc.model_dump(),
        },
        results=res_items,
        summary=SummaryBrief(
            best_mandi_id=summary_info.best_mandi_id,
            nearest_mandi_id=summary_info.nearest_mandi_id,
            extra_profit_q=summary_info.extra_profit_q,
            extra_profit_total=summary_info.extra_profit_total,
        ),
        assumptions=AssumptionsBrief(
            rates_status="ASSUMPTION_UNVERIFIED",
            market_fee_pct=round_currency(market_fee_pct),
            commission_pct=round_currency(commission_pct),
            vehicle=body.vehicle,
            rate_per_km=round_currency(rate_per_km),
            quality_cut_pct=round_currency(quality_cut_pct),
            round_trip_factor=Decimal("1.0"),
        ),
        warnings=warnings,
        meta=CompareMeta(
            elapsed_ms=round(elapsed_ms, 2),
            cache=CacheStatus(
                geocode="hit" if loc_res.cache_hit else "miss",
                distance=dist_cache_status,
                prices="hit" if price_cache_hit else "miss",
            ),
            generated_at=datetime.now(timezone.utc),
        ),
    )
