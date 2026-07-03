"""
FormulaIQ — FastF1 Season Data Fetcher (Module 1)
Fetches race results, qualifying, lap times, pit stops,
tyre compounds, sector times, weather data for seasons 2022–2025.

Usage:
    python fetch_season_data.py --season 2024
    python fetch_season_data.py --season 2022 --round 5
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import fastf1
import pandas as pd
from loguru import logger

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

# ── FastF1 Cache Setup ─────────────────────────────────────────────────────
CACHE_DIR = Path(settings.FASTF1_CACHE_DIR)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))


def get_schedule(season: int) -> pd.DataFrame:
    """Return the event schedule for a given season."""
    logger.info("Fetching schedule for season {}", season)
    schedule = fastf1.get_event_schedule(season, include_testing=False)
    return schedule


def fetch_race_session(season: int, round_number: int) -> Optional[fastf1.core.Session]:
    """Load a race session with all data enabled."""
    try:
        session = fastf1.get_session(season, round_number, "R")
        session.load(
            laps=True,
            telemetry=True,
            weather=True,
            messages=False,
        )
        logger.success("Loaded race | season={} round={} gp={}", season, round_number, session.event["EventName"])
        return session
    except Exception as exc:
        logger.error("Failed to load race | season={} round={} err={}", season, round_number, exc)
        return None


def fetch_qualifying_session(season: int, round_number: int) -> Optional[fastf1.core.Session]:
    """Load a qualifying session."""
    try:
        session = fastf1.get_session(season, round_number, "Q")
        session.load(laps=True, telemetry=False, weather=True, messages=False)
        logger.success("Loaded quali | season={} round={}", season, round_number)
        return session
    except Exception as exc:
        logger.error("Failed quali | season={} round={} err={}", season, round_number, exc)
        return None


def extract_race_results(session: fastf1.core.Session) -> pd.DataFrame:
    """Extract driver race results from a race session."""
    results = session.results.copy()
    if results is None or results.empty:
        return pd.DataFrame()

    results = results.rename(columns=str.lower)
    results["season"] = session.event["EventDate"].year
    results["round_number"] = session.event["RoundNumber"]
    results["grand_prix_name"] = session.event["EventName"]
    results["circuit_key"] = session.event.get("Location", "")
    results["race_date"] = session.event["EventDate"]

    # Clean finish position
    results["dnf"] = results.get("status", "Finished") != "Finished"

    keep_cols = [
        "season", "round_number", "grand_prix_name", "circuit_key", "race_date",
        "driverid", "abbreviation", "fullname", "teamid", "teamname",
        "gridposition", "position", "classifiedposition", "points",
        "fastestlap", "fastestlaptime", "status", "dnf",
        "time",
    ]
    existing = [c for c in keep_cols if c in results.columns]
    return results[existing].reset_index(drop=True)


def extract_qualifying_results(session: fastf1.core.Session) -> pd.DataFrame:
    """Extract qualifying lap times per driver."""
    results = session.results.copy()
    if results is None or results.empty:
        return pd.DataFrame()

    results["season"] = session.event["EventDate"].year
    results["round_number"] = session.event["RoundNumber"]
    results["grand_prix_name"] = session.event["EventName"]

    keep_cols = [
        "season", "round_number", "grand_prix_name",
        "DriverId", "Abbreviation", "FullName", "TeamId",
        "Q1", "Q2", "Q3", "Position",
    ]
    existing = [c for c in keep_cols if c in results.columns]
    return results[existing].reset_index(drop=True)


def extract_lap_times(session: fastf1.core.Session) -> pd.DataFrame:
    """Extract all lap times with sector times, tyre data."""
    laps = session.laps.copy()
    if laps is None or laps.empty:
        return pd.DataFrame()

    laps["season"] = session.event["EventDate"].year
    laps["round_number"] = session.event["RoundNumber"]
    laps["grand_prix_name"] = session.event["EventName"]

    # Convert timedelta to seconds
    for col in ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]:
        if col in laps.columns:
            laps[f"{col}Seconds"] = laps[col].dt.total_seconds()

    keep_cols = [
        "season", "round_number", "grand_prix_name",
        "Driver", "LapNumber",
        "LapTimeSeconds", "Sector1TimeSeconds", "Sector2TimeSeconds", "Sector3TimeSeconds",
        "Compound", "TyreLife", "IsPitOutLap", "IsPersonalBest",
        "TrackStatus", "Position",
    ]
    existing = [c for c in keep_cols if c in laps.columns]
    return laps[existing].reset_index(drop=True)


def extract_pit_stops(session: fastf1.core.Session) -> pd.DataFrame:
    """Extract pit stop data from lap data."""
    laps = session.laps.copy()
    if laps is None or laps.empty:
        return pd.DataFrame()

    pit_laps = laps[laps["PitOutTime"].notna() | laps["PitInTime"].notna()].copy()
    pit_laps["season"] = session.event["EventDate"].year
    pit_laps["round_number"] = session.event["RoundNumber"]
    pit_laps["grand_prix_name"] = session.event["EventName"]

    if "PitInTime" in pit_laps.columns and "PitOutTime" in pit_laps.columns:
        # Duration = time difference between PitIn and PitOut
        pit_laps["pit_duration_seconds"] = (
            pit_laps["PitOutTime"] - pit_laps["PitInTime"]
        ).dt.total_seconds().abs()

    return pit_laps.reset_index(drop=True)


def extract_weather(session: fastf1.core.Session) -> dict:
    """Extract averaged weather data from session."""
    weather = session.weather_data
    if weather is None or weather.empty:
        return {}

    summary = {
        "air_temp_avg": float(weather["AirTemp"].mean()),
        "air_temp_min": float(weather["AirTemp"].min()),
        "air_temp_max": float(weather["AirTemp"].max()),
        "track_temp_avg": float(weather["TrackTemp"].mean()),
        "track_temp_max": float(weather["TrackTemp"].max()),
        "humidity_avg": float(weather["Humidity"].mean()),
        "wind_speed_avg": float(weather["WindSpeed"].mean()),
        "wind_direction_avg": float(weather["WindDirection"].mean()),
        "rainfall": bool(weather["Rainfall"].any()),
        "pressure_avg": float(weather["Pressure"].mean()) if "Pressure" in weather else None,
        "condition": "wet" if bool(weather["Rainfall"].any()) else "dry",
    }
    return summary


def fetch_telemetry_for_lap(
    session: fastf1.core.Session,
    driver_code: str,
    lap_number: int,
) -> dict:
    """Extract telemetry channels for a specific driver + lap."""
    try:
        lap = session.laps.pick_driver(driver_code).pick_lap(lap_number).iloc[0]
        tel = lap.get_telemetry()
        if tel is None or tel.empty:
            return {}

        return {
            "driver_code": driver_code,
            "lap_number": lap_number,
            "speed_kmh": tel["Speed"].tolist(),
            "throttle_pct": tel["Throttle"].tolist(),
            "brake": tel["Brake"].tolist(),
            "gear": tel["nGear"].tolist(),
            "rpm": tel["RPM"].tolist(),
            "drs": tel["DRS"].tolist(),
            "x_pos": tel["X"].tolist(),
            "y_pos": tel["Y"].tolist(),
            "session_time": [t.total_seconds() for t in tel["SessionTime"]],
            "distance": tel["Distance"].tolist(),
        }
    except Exception as exc:
        logger.warning("Telemetry failed | driver={} lap={} err={}", driver_code, lap_number, exc)
        return {}


def fetch_full_season(season: int, rounds: Optional[list] = None) -> dict:
    """
    Orchestrates fetching all data for a season.
    Returns a dict of DataFrames ready for DB insertion.
    """
    logger.info("Starting full season fetch | season={}", season)
    schedule = get_schedule(season)

    all_race_results = []
    all_qualifying = []
    all_lap_times = []
    all_pit_stops = []
    all_weather = []

    for _, event in schedule.iterrows():
        round_num = int(event["RoundNumber"])
        gp_name = event["EventName"]

        if rounds and round_num not in rounds:
            continue

        logger.info("Processing | season={} round={} gp={}", season, round_num, gp_name)

        # ── Race session ───────────────────────────────────────────────────
        race_session = fetch_race_session(season, round_num)
        if race_session:
            race_results = extract_race_results(race_session)
            lap_times = extract_lap_times(race_session)
            pit_stops = extract_pit_stops(race_session)
            weather = extract_weather(race_session)

            all_race_results.append(race_results)
            all_lap_times.append(lap_times)
            all_pit_stops.append(pit_stops)
            if weather:
                weather["season"] = season
                weather["round_number"] = round_num
                weather["grand_prix_name"] = gp_name
                all_weather.append(weather)

        # ── Qualifying session ─────────────────────────────────────────────
        quali_session = fetch_qualifying_session(season, round_num)
        if quali_session:
            qualifying = extract_qualifying_results(quali_session)
            all_qualifying.append(qualifying)

    return {
        "race_results": pd.concat(all_race_results, ignore_index=True) if all_race_results else pd.DataFrame(),
        "qualifying": pd.concat(all_qualifying, ignore_index=True) if all_qualifying else pd.DataFrame(),
        "lap_times": pd.concat(all_lap_times, ignore_index=True) if all_lap_times else pd.DataFrame(),
        "pit_stops": pd.concat(all_pit_stops, ignore_index=True) if all_pit_stops else pd.DataFrame(),
        "weather": pd.DataFrame(all_weather) if all_weather else pd.DataFrame(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch F1 season data using FastF1")
    parser.add_argument("--season", type=int, required=True, help="F1 season year (2022-2025)")
    parser.add_argument("--rounds", type=int, nargs="+", help="Specific round numbers to fetch")
    args = parser.parse_args()

    data = fetch_full_season(args.season, args.rounds)

    for key, df in data.items():
        out_path = CACHE_DIR / f"{args.season}_{key}.csv"
        df.to_csv(out_path, index=False)
        logger.success("Saved {} rows to {}", len(df), out_path)
