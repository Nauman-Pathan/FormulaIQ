"""
FormulaIQ — Data Preprocessing & Normalization (Module 1)
Cleans, normalizes, and enriches the raw DataFrames
produced by fetch_season_data.py before DB insertion.
"""
import re
from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
VALID_COMPOUNDS = {"SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET", "UNKNOWN"}

DNF_STATUSES = {
    "Accident", "Collision", "Engine", "Gearbox", "Hydraulics",
    "Electrical", "Suspension", "Brakes", "Retired", "Withdrew",
    "Mechanical", "Power Unit", "Exhaust", "Puncture", "Spin",
    "Oil pressure", "Overheating",
}

TRACK_TYPES = {
    "Monaco": "street", "Singapore": "street", "Baku": "street", "Las Vegas": "street",
    "Jeddah": "street", "Miami": "street",
}


# ─────────────────────────────────────────────────────────────────────────────
# Race Results Preprocessing
# ─────────────────────────────────────────────────────────────────────────────
def preprocess_race_results(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize race results DataFrame."""
    if df.empty:
        return df

    df = df.copy()

    # Standardize column names
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    # Grid/finish positions: coerce to int, fill missing with 20
    for col in ["gridposition", "position"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(20).astype(int)

    # Points: numeric
    if "points" in df.columns:
        df["points"] = pd.to_numeric(df["points"], errors="coerce").fillna(0.0)

    # DNF flag
    if "status" in df.columns:
        df["dnf"] = df["status"].apply(
            lambda s: any(d.lower() in str(s).lower() for d in DNF_STATUSES)
        )

    # Fastest lap time: convert "1:23.456" → seconds
    if "fastestlaptime" in df.columns:
        df["fastest_lap_time_seconds"] = df["fastestlaptime"].apply(_parse_lap_time_str)

    # Driver code normalization: uppercase 3-letter
    if "abbreviation" in df.columns:
        df["driver_code"] = df["abbreviation"].str.upper().str[:3]

    logger.debug("Preprocessed race results | rows={}", len(df))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Qualifying Preprocessing
# ─────────────────────────────────────────────────────────────────────────────
def preprocess_qualifying(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize qualifying DataFrame: convert timedeltas to seconds."""
    if df.empty:
        return df

    df = df.copy()
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    for q_col in ["q1", "q2", "q3"]:
        if q_col in df.columns:
            df[f"{q_col}_seconds"] = df[q_col].apply(_timedelta_to_seconds)

    # Best qualifying time = min of q1/q2/q3
    q_cols = [f"{q}_seconds" for q in ["q1", "q2", "q3"] if f"{q}_seconds" in df.columns]
    if q_cols:
        df["best_qualifying_time_seconds"] = df[q_cols].min(axis=1)

    if "abbreviation" in df.columns:
        df["driver_code"] = df["abbreviation"].str.upper().str[:3]

    logger.debug("Preprocessed qualifying | rows={}", len(df))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Lap Times Preprocessing
# ─────────────────────────────────────────────────────────────────────────────
def preprocess_lap_times(df: pd.DataFrame) -> pd.DataFrame:
    """Clean lap time data, filter outliers, normalize tyre compounds."""
    if df.empty:
        return df

    df = df.copy()

    # Filter out in/out laps with extreme times
    if "LapTimeSeconds" in df.columns:
        lap_median = df["LapTimeSeconds"].median()
        df = df[df["LapTimeSeconds"] < lap_median * 2.0]  # Remove extreme outliers

    # Normalize compound names
    if "Compound" in df.columns:
        df["Compound"] = df["Compound"].str.upper().fillna("UNKNOWN")
        df.loc[~df["Compound"].isin(VALID_COMPOUNDS), "Compound"] = "UNKNOWN"

    # Boolean columns
    for bool_col in ["IsPitOutLap", "IsPersonalBest"]:
        if bool_col in df.columns:
            df[bool_col] = df[bool_col].fillna(False).astype(bool)

    # TyreLife numeric
    if "TyreLife" in df.columns:
        df["TyreLife"] = pd.to_numeric(df["TyreLife"], errors="coerce").fillna(0).astype(int)

    # Position numeric
    if "Position" in df.columns:
        df["Position"] = pd.to_numeric(df["Position"], errors="coerce").fillna(20).astype(int)

    logger.debug("Preprocessed lap times | rows={}", len(df))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Pit Stop Preprocessing
# ─────────────────────────────────────────────────────────────────────────────
def preprocess_pit_stops(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize pit stop records."""
    if df.empty:
        return df

    df = df.copy()

    if "pit_duration_seconds" in df.columns:
        # Filter implausible durations (< 15s or > 120s)
        df = df[(df["pit_duration_seconds"] > 15) & (df["pit_duration_seconds"] < 120)]

    logger.debug("Preprocessed pit stops | rows={}", len(df))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Weather Preprocessing
# ─────────────────────────────────────────────────────────────────────────────
def preprocess_weather(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize weather data."""
    if df.empty:
        return df

    df = df.copy()

    for col in ["air_temp_avg", "track_temp_avg", "humidity_avg", "wind_speed_avg"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "rainfall" in df.columns:
        df["rainfall"] = df["rainfall"].fillna(False).astype(bool)
        df["condition"] = df["rainfall"].apply(lambda r: "wet" if r else "dry")

    logger.debug("Preprocessed weather | rows={}", len(df))
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Feature Engineering: Derive circuit features
# ─────────────────────────────────────────────────────────────────────────────
def enrich_circuit_features(df: pd.DataFrame, gp_name_col: str = "grand_prix_name") -> pd.DataFrame:
    """Add track_type based on GP name."""
    if gp_name_col not in df.columns:
        return df

    def get_track_type(gp_name: str) -> str:
        for keyword, ttype in TRACK_TYPES.items():
            if keyword.lower() in str(gp_name).lower():
                return ttype
        return "permanent"

    df["track_type"] = df[gp_name_col].apply(get_track_type)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────────
def _parse_lap_time_str(time_str) -> Optional[float]:
    """Convert '1:23.456' or '83.456' string to seconds."""
    if pd.isna(time_str):
        return None
    try:
        time_str = str(time_str)
        if ":" in time_str:
            parts = time_str.strip().split(":")
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        return float(time_str)
    except (ValueError, IndexError):
        return None


def _timedelta_to_seconds(td) -> Optional[float]:
    """Convert pandas Timedelta or NaT to seconds float."""
    if pd.isna(td):
        return None
    try:
        return td.total_seconds()
    except AttributeError:
        return _parse_lap_time_str(td)


def preprocess_all(raw_data: dict) -> dict:
    """Apply all preprocessing steps to a raw data dict."""
    return {
        "race_results": preprocess_race_results(raw_data.get("race_results", pd.DataFrame())),
        "qualifying": preprocess_qualifying(raw_data.get("qualifying", pd.DataFrame())),
        "lap_times": preprocess_lap_times(raw_data.get("lap_times", pd.DataFrame())),
        "pit_stops": preprocess_pit_stops(raw_data.get("pit_stops", pd.DataFrame())),
        "weather": preprocess_weather(raw_data.get("weather", pd.DataFrame())),
    }
