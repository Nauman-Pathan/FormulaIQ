"""
FormulaIQ — Drivers API Router (Module 5)
GET /drivers
GET /driver-analysis/{driver}
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database.db import get_async_db, SyncSessionLocal
from models.orm import Driver
from models.schemas import DriverAnalyticsOut
from services.driver_service import compute_driver_analytics
from utils.cache import cache_get, cache_set, make_cache_key

router = APIRouter(tags=["Drivers"])


@router.get("/drivers", summary="List all drivers", response_model=List[dict])
async def list_drivers(
    season: Optional[int] = Query(None, ge=2022, le=2026),
    db: AsyncSession = Depends(get_async_db),
):
    """Return all drivers, optionally filtered by season."""
    cache_key = make_cache_key("drivers", season or "all")
    cached = await cache_get(cache_key)
    if cached:
        return cached

    stmt = select(Driver).order_by(Driver.season.desc(), Driver.full_name)
    if season:
        stmt = stmt.where(Driver.season == season)

    result = await db.execute(stmt)
    drivers = result.scalars().all()

    data = [
        {
            "id": d.id,
            "driver_code": d.driver_code,
            "full_name": d.full_name,
            "nationality": d.nationality,
            "driver_number": d.driver_number,
            "season": d.season,
        }
        for d in drivers
    ]
    await cache_set(cache_key, data, ttl=3600)
    return data


@router.get(
    "/driver-analysis/{driver}",
    response_model=DriverAnalyticsOut,
    summary="Get advanced driver analytics",
    description=(
        "Computes consistency score, overtaking efficiency, tyre management, "
        "qualifying performance, and composite racecraft score for a given driver."
    ),
)
async def get_driver_analysis(
    driver: str,
    season: Optional[int] = Query(None, ge=2022, le=2026),
):
    """Compute and return advanced driver performance metrics."""
    driver_code = driver.upper()
    cache_key = make_cache_key("driver_analysis", driver_code, season or "all")
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        # Driver analytics requires complex SQL with joins, use sync session
        with SyncSessionLocal() as db:
            analytics = compute_driver_analytics(db, driver_code, season)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Driver analytics error | driver={} err={}", driver_code, exc)
        raise HTTPException(status_code=500, detail="Analytics computation failed")

    await cache_set(cache_key, analytics, ttl=600)
    return analytics
