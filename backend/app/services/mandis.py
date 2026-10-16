from datetime import date, timedelta
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.geo import haversine_distance_km
from app.models import Mandi, Price

logger = logging.getLogger(__name__)

SEED_PATHS = [
    Path(__file__).resolve().parent.parent.parent / "data" / "mandis.seed.json",
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "mandis.seed.json",
]

async def load_seed_into_db(
    db: AsyncSession, seed_file: Optional[Path] = None
) -> int:
    """Load mandis from seed JSON into the database idempotently."""
    path = seed_file
    if not path:
        for p in SEED_PATHS:
            if p.exists():
                path = p
                break

    if not path or not path.exists():
        logger.warning("No mandi seed file found to load.")
        return 0

    with open(path, "r", encoding="utf-8") as f:
        records: List[Dict[str, Any]] = json.load(f)

    inserted_or_updated = 0
    for r in records:
        stmt = select(Mandi).where(
            Mandi.state == r["state"],
            Mandi.district == r["district"],
            Mandi.name == r["name"],
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()

        if existing:
            existing.lat = float(r["lat"])
            existing.lng = float(r["lng"])
            existing.geocode_source = str(r["geocode_source"])
            existing.geocode_confidence = float(r["geocode_confidence"]) if r.get("geocode_confidence") is not None else None
            existing.needs_review = bool(r["needs_review"])
        else:
            new_mandi = Mandi(
                state=r["state"],
                district=r["district"],
                name=r["name"],
                lat=float(r["lat"]),
                lng=float(r["lng"]),
                geocode_source=str(r["geocode_source"]),
                geocode_confidence=float(r["geocode_confidence"]) if r.get("geocode_confidence") is not None else None,
                needs_review=bool(r["needs_review"]),
            )
            db.add(new_mandi)
        inserted_or_updated += 1

    await db.commit()
    logger.info(f"Loaded/updated {inserted_or_updated} mandis from {path}")
    return inserted_or_updated

async def get_candidate_mandis(
    db: AsyncSession,
    origin_lat: float,
    origin_lng: float,
    commodity: str,
    max_radius_km: float = 150.0,
    max_age_days: int = 3,
    limit: int = 10,
    reference_date: Optional[date] = None,
) -> List[Tuple[Mandi, Price, float]]:
    """
    Find nearest mandis within max_radius_km that have a price for commodity within max_age_days.
    Returns list of (Mandi, Price, haversine_km) sorted by distance.
    """
    ref_date = reference_date or date.today()
    min_date = ref_date - timedelta(days=max_age_days)

    # 1. Fetch all mandis that have coordinates
    stmt = select(Mandi).where(Mandi.lat != 0.0, Mandi.lng != 0.0)
    result = await db.execute(stmt)
    all_mandis = result.scalars().all()

    # 2. Filter mandis by haversine distance within max_radius_km
    mandi_distances: List[Tuple[Mandi, float]] = []
    for m in all_mandis:
        dist = haversine_distance_km(origin_lat, origin_lng, m.lat, m.lng)
        if dist <= max_radius_km:
            mandi_distances.append((m, dist))

    if not mandi_distances:
        return []

    # Sort candidates by initial haversine distance
    mandi_distances.sort(key=lambda x: x[1])

    # 3. For candidate mandis, fetch the latest price for the commodity within max_age_days
    candidates: List[Tuple[Mandi, Price, float]] = []
    for mandi, dist in mandi_distances:
        # Get latest price for this commodity
        price_stmt = (
            select(Price)
            .where(
                Price.mandi_id == mandi.id,
                func.lower(Price.commodity) == commodity.lower(),
                Price.arrival_date >= min_date,
            )
            .order_by(Price.arrival_date.desc(), Price.id.desc())
            .limit(1)
        )
        price_res = await db.execute(price_stmt)
        price = price_res.scalar_one_or_none()

        if price:
            candidates.append((mandi, price, dist))
            if len(candidates) >= limit:
                break

    return candidates
