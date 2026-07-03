"""
FormulaIQ — Telemetry API Router (Module 2)
GET /telemetry/{year}/{grand_prix}/{driver1}/{driver2}
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from services.telemetry_service import get_telemetry_comparison
from utils.cache import cache_get, cache_set, make_cache_key

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.get(
    "/{year}/{grand_prix}/{driver1}/{driver2}",
    summary="Compare telemetry between two drivers",
    description=(
        "Fetches FastF1 telemetry for two drivers from a given race. "
        "Returns speed, throttle, brake, gear, DRS, lap delta, and sector comparison."
    ),
)
async def get_driver_telemetry(
    year: int,
    grand_prix: str,
    driver1: str,
    driver2: str,
    lap: Optional[int] = Query(None, ge=1, le=78, description="Specific lap number; omit for fastest lap"),
):
    """Compare telemetry data between two drivers in a specified race."""
    cache_key = make_cache_key("telemetry", year, grand_prix, driver1, driver2, lap or "fastest")
    cached = await cache_get(cache_key)
    if cached:
        return cached

    try:
        result = get_telemetry_comparison(
            year=year,
            grand_prix=grand_prix,
            driver1=driver1,
            driver2=driver2,
            lap_number=lap,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Telemetry error | {}", exc)
        raise HTTPException(status_code=500, detail="Failed to fetch telemetry data")

    # Cache for 10 minutes (telemetry doesn't change)
    await cache_set(cache_key, result, ttl=600)
    return result
