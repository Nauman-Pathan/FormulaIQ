"""
FormulaIQ — Feature Engineering for Race Prediction (Module 3)
Transforms raw DB data into an ML-ready feature matrix for XGBoost.
"""
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

COMPOUND_MAP = {"SOFT": 0, "MEDIUM": 1, "HARD": 2, "INTERMEDIATE": 3, "WET": 4, "UNKNOWN": 5}
TRACK_TYPE_MAP = {"permanent": 0, "street": 1, "hybrid": 2}
WEATHER_MAP = {"dry": 0, "mixed": 1, "wet": 2}


def build_feature_matrix(
    race_results: pd.DataFrame,
    qualifying: pd.DataFrame,
    lap_times: pd.DataFrame,
    pit_stops: pd.DataFrame,
    weather: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the full feature matrix for model training.
    Each row = one driver in one race.
    """
    if race_results.empty:
        return pd.DataFrame()

    logger.info("Building feature matrix | races={}", race_results["race_id"].nunique())

    features = race_results[
        ["race_id", "driver_id", "grid_position", "finish_position",
         "points_scored", "dnf", "season"]
    ].copy()

    # ── Qualifying features ─────────────────────────────────────────────────
    if not qualifying.empty:
        q_feat = qualifying[["race_id", "driver_id", "best_qualifying_time_seconds", "grid_position"]].copy()
        q_feat = q_feat.rename(columns={"grid_position": "q_grid_position"})
        features = features.merge(q_feat, on=["race_id", "driver_id"], how="left")
    else:
        features["best_qualifying_time_seconds"] = np.nan

    # ── Lap time features: avg pace, consistency ────────────────────────────
    if not lap_times.empty:
        lap_feat = (
            lap_times[lap_times["lap_time_seconds"].between(60, 120)]
            .groupby(["race_id", "driver_id"])
            .agg(
                avg_lap_time=("lap_time_seconds", "mean"),
                lap_std=("lap_time_seconds", "std"),
                avg_sector1=("sector1_seconds", "mean"),
                avg_sector2=("sector2_seconds", "mean"),
                avg_sector3=("sector3_seconds", "mean"),
                laps_completed=("lap_number", "max"),
            )
            .reset_index()
        )
        # Consistency = 1 / (std / mean), higher is better
        lap_feat["consistency_score"] = 1.0 / (lap_feat["lap_std"] / lap_feat["avg_lap_time"] + 1e-6)
        features = features.merge(lap_feat, on=["race_id", "driver_id"], how="left")
    else:
        for col in ["avg_lap_time", "lap_std", "consistency_score", "laps_completed"]:
            features[col] = np.nan

    # ── Pit stop features ───────────────────────────────────────────────────
    if not pit_stops.empty:
        pit_feat = (
            pit_stops.groupby(["race_id", "driver_id"])
            .agg(
                num_pit_stops=("stop_number", "max"),
                avg_pit_duration=("pit_duration_seconds", "mean"),
            )
            .reset_index()
        )
        features = features.merge(pit_feat, on=["race_id", "driver_id"], how="left")
    else:
        features["num_pit_stops"] = np.nan
        features["avg_pit_duration"] = np.nan

    # ── Weather features ────────────────────────────────────────────────────
    if not weather.empty:
        w_feat = weather[["race_id", "air_temp_avg", "track_temp_avg", "humidity_avg", "rainfall", "condition"]].copy()
        w_feat["weather_code"] = w_feat["condition"].map(WEATHER_MAP).fillna(0)
        w_feat["rainfall"] = w_feat["rainfall"].astype(int)
        features = features.merge(w_feat, on="race_id", how="left")
    else:
        features["air_temp_avg"] = np.nan
        features["weather_code"] = 0
        features["rainfall"] = 0

    # ── Rolling performance (previous 3 races avg finish) ───────────────────
    features = features.sort_values(["driver_id", "race_id"])
    features["prev3_avg_finish"] = (
        features.groupby("driver_id")["finish_position"]
        .transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    )

    # ── Cumulative points in season ─────────────────────────────────────────
    features["cumulative_points"] = (
        features.groupby(["driver_id", "season"])["points_scored"]
        .transform(lambda s: s.shift(1).cumsum().fillna(0))
    )

    # ── Grid position delta (qualify vs grid — penalties, etc.) ────────────
    if "q_grid_position" in features.columns:
        features["grid_delta"] = features["grid_position"] - features.get("q_grid_position", features["grid_position"])
    else:
        features["grid_delta"] = 0

    # ── Fill NaN with sensible defaults ────────────────────────────────────
    fill_defaults = {
        "best_qualifying_time_seconds": features["best_qualifying_time_seconds"].median(),
        "avg_lap_time": features.get("avg_lap_time", pd.Series()).median(),
        "consistency_score": 50.0,
        "num_pit_stops": 2,
        "avg_pit_duration": 25.0,
        "prev3_avg_finish": 10.0,
        "cumulative_points": 0,
        "air_temp_avg": 25.0,
        "track_temp_avg": 40.0,
        "humidity_avg": 50.0,
        "weather_code": 0,
        "rainfall": 0,
        "grid_delta": 0,
    }
    features = features.fillna(fill_defaults)

    logger.info("Feature matrix built | shape={}", features.shape)
    return features


FEATURE_COLUMNS = [
    "grid_position",
    "best_qualifying_time_seconds",
    "consistency_score",
    "avg_lap_time",
    "prev3_avg_finish",
    "cumulative_points",
    "num_pit_stops",
    "avg_pit_duration",
    "weather_code",
    "rainfall",
    "air_temp_avg",
    "track_temp_avg",
    "humidity_avg",
    "grid_delta",
    "laps_completed",
]

TARGET_COLUMN = "finish_position"
