"""
FormulaIQ — Database Persistence Layer (Module 1)
Saves preprocessed DataFrames into PostgreSQL using SQLAlchemy bulk operations.

Usage:
    python save_to_db.py --season 2024
"""
import argparse
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_pipeline.fetch_season_data import fetch_full_season
from data_pipeline.preprocess_data import preprocess_all
from database.db import SyncSessionLocal, sync_engine
from models.orm import (
    Base, Circuit, Constructor, Driver, LapTime, ModelPrediction,
    PitStop, Qualifying, Race, RaceResult, Telemetry, Weather,
)


def init_db():
    """Create all tables if they don't exist."""
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=sync_engine)
    logger.success("Database schema ready.")


def upsert_circuit(db: Session, circuit_key: str, name: str, **kwargs) -> Circuit:
    """Get or create a circuit record."""
    circuit = db.query(Circuit).filter_by(circuit_key=circuit_key).first()
    if not circuit:
        circuit = Circuit(circuit_key=circuit_key, name=name, **kwargs)
        db.add(circuit)
        db.flush()
    return circuit


def upsert_race(db: Session, season: int, round_number: int, gp_name: str, circuit_id: Optional[int], race_date) -> Race:
    """Get or create a race record."""
    race = db.query(Race).filter_by(season=season, round_number=round_number).first()
    if not race:
        race = Race(
            season=season,
            round_number=round_number,
            grand_prix_name=gp_name,
            grand_prix_key=gp_name.lower().replace(" ", "_"),
            circuit_id=circuit_id,
            race_date=race_date,
            session_status="completed",
        )
        db.add(race)
        db.flush()
    return race


def upsert_driver(db: Session, driver_code: str, full_name: str, season: int, **kwargs) -> Driver:
    """Get or create a driver record."""
    driver = db.query(Driver).filter_by(driver_code=driver_code, season=season).first()
    if not driver:
        driver = Driver(
            driver_code=driver_code,
            full_name=full_name,
            driver_number=kwargs.get("driver_number", 99),
            season=season,
        )
        db.add(driver)
        db.flush()
    return driver


def upsert_constructor(db: Session, constructor_key: str, name: str) -> Constructor:
    """Get or create a constructor record."""
    ctor = db.query(Constructor).filter_by(constructor_key=constructor_key).first()
    if not ctor:
        ctor = Constructor(constructor_key=constructor_key, name=name)
        db.add(ctor)
        db.flush()
    return ctor


def save_race_results(db: Session, df: pd.DataFrame) -> int:
    """Bulk save race results."""
    if df.empty:
        return 0

    saved = 0
    seasons_rounds = df[["season", "round_number", "grand_prix_name", "circuit_key", "race_date"]].drop_duplicates()

    for _, sr in seasons_rounds.iterrows():
        circuit = upsert_circuit(db, str(sr["circuit_key"]), str(sr["circuit_key"]).replace("_", " "))
        race = upsert_race(db, int(sr["season"]), int(sr["round_number"]), str(sr["grand_prix_name"]), circuit.id, sr["race_date"])

        race_df = df[(df["season"] == sr["season"]) & (df["round_number"] == sr["round_number"])]
        for _, row in race_df.iterrows():
            driver_code = str(row.get("driver_code", row.get("abbreviation", "UNK")))[:3].upper()
            full_name = str(row.get("fullname", driver_code))
            driver = upsert_driver(db, driver_code, full_name, int(sr["season"]))

            # Check for duplicate
            existing = db.query(RaceResult).filter_by(race_id=race.id, driver_id=driver.id).first()
            if existing:
                continue

            result = RaceResult(
                race_id=race.id,
                driver_id=driver.id,
                grid_position=int(row.get("gridposition", 20)),
                finish_position=int(row.get("position", 20)),
                classified_position=str(row.get("classifiedposition", "")),
                points_scored=float(row.get("points", 0.0)),
                fastest_lap=bool(row.get("fastestlap", False)),
                fastest_lap_time_seconds=row.get("fastest_lap_time_seconds"),
                status=str(row.get("status", "Finished")),
                dnf=bool(row.get("dnf", False)),
            )
            db.add(result)
            saved += 1

    db.commit()
    logger.success("Saved {} race results", saved)
    return saved


def save_qualifying(db: Session, df: pd.DataFrame) -> int:
    """Bulk save qualifying results."""
    if df.empty:
        return 0

    saved = 0
    for _, row in df.iterrows():
        season = int(row.get("season", 0))
        round_num = int(row.get("round_number", 0))
        driver_code = str(row.get("driver_code", row.get("abbreviation", "UNK")))[:3].upper()

        race = db.query(Race).filter_by(season=season, round_number=round_num).first()
        driver = db.query(Driver).filter_by(driver_code=driver_code, season=season).first()

        if not race or not driver:
            continue

        existing = db.query(Qualifying).filter_by(race_id=race.id, driver_id=driver.id).first()
        if existing:
            continue

        q = Qualifying(
            race_id=race.id,
            driver_id=driver.id,
            q1_time_seconds=row.get("q1_seconds"),
            q2_time_seconds=row.get("q2_seconds"),
            q3_time_seconds=row.get("q3_seconds"),
            best_qualifying_time_seconds=row.get("best_qualifying_time_seconds"),
            grid_position=int(row.get("position", 20)) if pd.notna(row.get("position")) else None,
        )
        db.add(q)
        saved += 1

    db.commit()
    logger.success("Saved {} qualifying records", saved)
    return saved


def save_lap_times(db: Session, df: pd.DataFrame) -> int:
    """Bulk save lap times in batches."""
    if df.empty:
        return 0

    records = []
    for _, row in df.iterrows():
        season = int(row.get("season", 0))
        round_num = int(row.get("round_number", 0))
        driver_code = str(row.get("Driver", "UNK"))[:3].upper()

        race = db.query(Race).filter_by(season=season, round_number=round_num).first()
        driver = db.query(Driver).filter_by(driver_code=driver_code, season=season).first()

        if not race or not driver:
            continue

        records.append({
            "race_id": race.id,
            "driver_id": driver.id,
            "lap_number": int(row.get("LapNumber", 0)),
            "lap_time_seconds": row.get("LapTimeSeconds"),
            "sector1_seconds": row.get("Sector1TimeSeconds"),
            "sector2_seconds": row.get("Sector2TimeSeconds"),
            "sector3_seconds": row.get("Sector3TimeSeconds"),
            "compound": str(row.get("Compound", "UNKNOWN")),
            "tyre_life": int(row.get("TyreLife", 0)),
            "is_pit_out_lap": bool(row.get("IsPitOutLap", False)),
            "is_personal_best": bool(row.get("IsPersonalBest", False)),
            "track_status": str(row.get("TrackStatus", "1")),
            "position": int(row.get("Position", 20)),
        })

    # Batch insert with ON CONFLICT DO NOTHING
    if records:
        stmt = pg_insert(LapTime.__table__).values(records)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["race_id", "driver_id", "lap_number"]
        )
        db.execute(stmt)
        db.commit()

    logger.success("Saved {} lap time records", len(records))
    return len(records)


def save_weather(db: Session, df: pd.DataFrame) -> int:
    """Save weather records."""
    if df.empty:
        return 0

    saved = 0
    for _, row in df.iterrows():
        season = int(row.get("season", 0))
        round_num = int(row.get("round_number", 0))
        race = db.query(Race).filter_by(season=season, round_number=round_num).first()
        if not race:
            continue

        existing = db.query(Weather).filter_by(race_id=race.id).first()
        if existing:
            continue

        w = Weather(
            race_id=race.id,
            air_temp_avg=row.get("air_temp_avg"),
            air_temp_min=row.get("air_temp_min"),
            air_temp_max=row.get("air_temp_max"),
            track_temp_avg=row.get("track_temp_avg"),
            track_temp_max=row.get("track_temp_max"),
            humidity_avg=row.get("humidity_avg"),
            wind_speed_avg=row.get("wind_speed_avg"),
            wind_direction_avg=row.get("wind_direction_avg"),
            rainfall=bool(row.get("rainfall", False)),
            pressure_avg=row.get("pressure_avg"),
            condition=str(row.get("condition", "dry")),
        )
        db.add(w)
        saved += 1

    db.commit()
    logger.success("Saved {} weather records", saved)
    return saved


def run_pipeline(season: int, rounds: Optional[list] = None):
    """Full ETL pipeline: fetch → preprocess → save."""
    logger.info("=== FormulaIQ ETL Pipeline | season={} ===", season)

    init_db()

    logger.info("Step 1/3: Fetching data from FastF1...")
    raw_data = fetch_full_season(season, rounds)

    logger.info("Step 2/3: Preprocessing data...")
    clean_data = preprocess_all(raw_data)

    logger.info("Step 3/3: Saving to PostgreSQL...")
    with SyncSessionLocal() as db:
        save_race_results(db, clean_data["race_results"])
        save_qualifying(db, clean_data["qualifying"])
        save_lap_times(db, clean_data["lap_times"])
        save_weather(db, clean_data["weather"])

    logger.success("=== ETL Pipeline Complete | season={} ===", season)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ETL pipeline: FastF1 → PostgreSQL")
    parser.add_argument("--season", type=int, required=True, help="Season year (2022-2025)")
    parser.add_argument("--rounds", type=int, nargs="+", help="Specific rounds")
    args = parser.parse_args()

    run_pipeline(args.season, args.rounds)
