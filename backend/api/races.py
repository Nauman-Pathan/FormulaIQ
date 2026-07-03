"""
FormulaIQ — Races & Results API Router
GET /races
GET /races/{race_id}/results
GET /historical-results
GET /circuits
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database.db import get_async_db
from models.orm import Circuit, Race, RaceResult, Driver, Constructor
from models.schemas import CircuitOut, RaceOut
from utils.cache import cache_get, cache_set, make_cache_key

router = APIRouter(tags=["Races"])


@router.get("/races", summary="List all races", response_model=List[dict])
async def list_races(
    season: Optional[int] = Query(None, ge=2022, le=2026),
    db: AsyncSession = Depends(get_async_db),
):
    """Return all races, optionally filtered by season."""
    cache_key = make_cache_key("races", season or "all")
    cached = await cache_get(cache_key)
    if cached:
        return cached

    stmt = select(Race).order_by(Race.season.desc(), Race.round_number)
    if season:
        stmt = stmt.where(Race.season == season)

    result = await db.execute(stmt)
    races = result.scalars().all()

    data = [
        {
            "id": r.id,
            "season": r.season,
            "round_number": r.round_number,
            "grand_prix_name": r.grand_prix_name,
            "grand_prix_key": r.grand_prix_key,
            "race_date": str(r.race_date),
            "session_status": r.session_status,
        }
        for r in races
    ]
    await cache_set(cache_key, data, ttl=3600)
    return data


@router.get("/races/{race_id}/results", summary="Get race results for a specific race")
async def get_race_results(race_id: int, db: AsyncSession = Depends(get_async_db)):
    """Return all driver results for a race."""
    cache_key = make_cache_key("race_results", race_id)
    cached = await cache_get(cache_key)
    if cached:
        return cached

    stmt = (
        select(RaceResult, Driver, Constructor)
        .join(Driver, RaceResult.driver_id == Driver.id)
        .outerjoin(Constructor, RaceResult.constructor_id == Constructor.id)
        .where(RaceResult.race_id == race_id)
        .order_by(RaceResult.finish_position)
    )
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        raise HTTPException(status_code=404, detail=f"No results for race_id={race_id}")

    data = [
        {
            "driver_code": driver.driver_code,
            "driver_name": driver.full_name,
            "constructor": ctor.name if ctor else "",
            "grid_position": rr.grid_position,
            "finish_position": rr.finish_position,
            "classified_position": rr.classified_position,
            "points_scored": rr.points_scored,
            "fastest_lap": rr.fastest_lap,
            "status": rr.status,
            "dnf": rr.dnf,
        }
        for rr, driver, ctor in rows
    ]
    await cache_set(cache_key, data, ttl=3600)
    return data


@router.get("/circuits", summary="List all circuits")
async def list_circuits(db: AsyncSession = Depends(get_async_db)):
    """Return all circuit records."""
    cache_key = make_cache_key("circuits")
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = await db.execute(select(Circuit).order_by(Circuit.name))
    circuits = result.scalars().all()

    data = [
        {
            "id": c.id,
            "circuit_key": c.circuit_key,
            "name": c.name,
            "location": c.location,
            "country": c.country,
            "track_length_km": c.track_length_km,
            "track_type": c.track_type,
            "lap_record_seconds": c.lap_record_seconds,
        }
        for c in circuits
    ]
    await cache_set(cache_key, data, ttl=86400)
    return data


@router.get("/historical-results", summary="Query historical race results with filters")
async def get_historical_results(
    driver_code: Optional[str] = Query(None, min_length=2, max_length=4),
    season: Optional[int] = Query(None, ge=2022, le=2026),
    grand_prix: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_async_db),
):
    """Flexible historical results query with optional filters."""
    stmt = (
        select(RaceResult, Driver, Race, Constructor)
        .join(Driver, RaceResult.driver_id == Driver.id)
        .join(Race, RaceResult.race_id == Race.id)
        .outerjoin(Constructor, RaceResult.constructor_id == Constructor.id)
        .order_by(Race.season.desc(), Race.round_number)
        .limit(limit)
    )

    if driver_code:
        stmt = stmt.where(Driver.driver_code == driver_code.upper())
    if season:
        stmt = stmt.where(Race.season == season)
    if grand_prix:
        stmt = stmt.where(Race.grand_prix_name.ilike(f"%{grand_prix}%"))

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "season": race.season,
            "round_number": race.round_number,
            "grand_prix_name": race.grand_prix_name,
            "driver_code": driver.driver_code,
            "driver_name": driver.full_name,
            "constructor": ctor.name if ctor else "",
            "grid_position": rr.grid_position,
            "finish_position": rr.finish_position,
            "points_scored": rr.points_scored,
            "dnf": rr.dnf,
            "status": rr.status,
        }
        for rr, driver, race, ctor in rows
    ]
