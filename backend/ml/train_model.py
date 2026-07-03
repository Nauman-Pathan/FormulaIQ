"""
FormulaIQ — XGBoost Model Training (Module 3)
Trains a multi-output race position predictor.
Saves model artifacts for inference.

Usage:
    python train_model.py --seasons 2022 2023 2024
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier, XGBRegressor

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from database.db import SyncSessionLocal
from ml.feature_engineering import FEATURE_COLUMNS, TARGET_COLUMN, build_feature_matrix
from models.orm import LapTime, PitStop, Qualifying, Race, RaceResult, Weather

MODEL_DIR = Path(settings.MODEL_DIR)
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_training_data(seasons: List[int]) -> dict:
    """Load all required DataFrames from PostgreSQL for given seasons."""
    logger.info("Loading training data | seasons={}", seasons)
    with SyncSessionLocal() as db:
        race_ids = [
            r.id for r in db.query(Race.id).filter(Race.season.in_(seasons)).all()
        ]
        if not race_ids:
            logger.warning("No races found for seasons {}", seasons)
            return {}

        def to_df(query_result, columns):
            return pd.DataFrame([dict(zip(columns, row)) for row in query_result])

        # Race results
        rr_rows = db.execute(
            f"""SELECT id, race_id, driver_id, grid_position, finish_position,
                       points_scored, dnf, season
                FROM race_results
                JOIN races ON races.id = race_results.race_id
                WHERE race_results.race_id IN ({','.join(map(str,race_ids))})"""
        ).fetchall()
        race_results_df = to_df(rr_rows, [
            "id", "race_id", "driver_id", "grid_position", "finish_position",
            "points_scored", "dnf", "season"
        ])

        # Qualifying
        q_rows = db.execute(
            f"""SELECT race_id, driver_id, best_qualifying_time_seconds, grid_position
                FROM qualifying WHERE race_id IN ({','.join(map(str,race_ids))})"""
        ).fetchall()
        qualifying_df = to_df(q_rows, ["race_id", "driver_id", "best_qualifying_time_seconds", "grid_position"])

        # Lap times (aggregate only)
        lt_rows = db.execute(
            f"""SELECT race_id, driver_id, lap_number, lap_time_seconds,
                       sector1_seconds, sector2_seconds, sector3_seconds
                FROM lap_times WHERE race_id IN ({','.join(map(str,race_ids))})"""
        ).fetchall()
        lap_times_df = to_df(lt_rows, [
            "race_id", "driver_id", "lap_number", "lap_time_seconds",
            "sector1_seconds", "sector2_seconds", "sector3_seconds"
        ])

        # Pit stops
        ps_rows = db.execute(
            f"""SELECT race_id, driver_id, stop_number, pit_duration_seconds
                FROM pit_stops WHERE race_id IN ({','.join(map(str,race_ids))})"""
        ).fetchall()
        pit_stops_df = to_df(ps_rows, ["race_id", "driver_id", "stop_number", "pit_duration_seconds"])

        # Weather
        w_rows = db.execute(
            f"""SELECT race_id, air_temp_avg, track_temp_avg, humidity_avg, rainfall, condition
                FROM weather WHERE race_id IN ({','.join(map(str,race_ids))})"""
        ).fetchall()
        weather_df = to_df(w_rows, ["race_id", "air_temp_avg", "track_temp_avg", "humidity_avg", "rainfall", "condition"])

    return {
        "race_results": race_results_df,
        "qualifying": qualifying_df,
        "lap_times": lap_times_df,
        "pit_stops": pit_stops_df,
        "weather": weather_df,
    }


def train_position_model(X: np.ndarray, y: np.ndarray) -> XGBRegressor:
    """Train XGBoost regressor to predict finishing position."""
    model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=1.0,
        objective="reg:squarederror",
        eval_metric="mae",
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )

    # Cross-validation
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X, y, cv=kf, scoring="neg_mean_absolute_error")
    logger.info("CV MAE = {:.3f} ± {:.3f}", -cv_scores.mean(), cv_scores.std())

    model.fit(X, y, eval_set=[(X, y)], verbose=False)
    return model


def train_dnf_model(X: np.ndarray, y_dnf: np.ndarray) -> XGBClassifier:
    """Train XGBoost classifier for DNF probability."""
    model = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.8,
        scale_pos_weight=10,  # DNF is rare class
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
        verbosity=0,
    )
    model.fit(X, y_dnf)
    return model


def save_model_artifacts(
    position_model: XGBRegressor,
    dnf_model: XGBClassifier,
    feature_columns: List[str],
    metrics: dict,
    version: str = "v1",
):
    """Persist models and metadata to disk."""
    joblib.dump(position_model, MODEL_DIR / f"position_model_{version}.joblib")
    joblib.dump(dnf_model, MODEL_DIR / f"dnf_model_{version}.joblib")

    metadata = {
        "version": version,
        "feature_columns": feature_columns,
        "metrics": metrics,
        "feature_importances": {
            col: float(imp)
            for col, imp in zip(feature_columns, position_model.feature_importances_)
        },
    }
    with open(MODEL_DIR / f"model_metadata_{version}.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.success("Model artifacts saved | dir={} version={}", MODEL_DIR, version)


def run_training(seasons: List[int], version: str = "v1"):
    """Full training pipeline."""
    logger.info("=== FormulaIQ Model Training | seasons={} ===", seasons)

    data = load_training_data(seasons)
    if not data:
        logger.error("No data to train on. Run ETL pipeline first.")
        return

    features_df = build_feature_matrix(**data)
    if features_df.empty:
        logger.error("Feature matrix is empty.")
        return

    available_cols = [c for c in FEATURE_COLUMNS if c in features_df.columns]
    X = features_df[available_cols].values
    y_pos = features_df[TARGET_COLUMN].values
    y_dnf = features_df["dnf"].astype(int).values

    logger.info("Training data | X={} features, {} samples", len(available_cols), len(X))

    # Train models
    position_model = train_position_model(X, y_pos)
    dnf_model = train_dnf_model(X, y_dnf)

    # Evaluate
    pos_pred = position_model.predict(X)
    mae = mean_absolute_error(y_pos, pos_pred)
    logger.info("Training MAE (positions) = {:.3f}", mae)

    metrics = {"mae_positions": mae, "training_samples": len(X), "seasons": seasons}

    save_model_artifacts(position_model, dnf_model, available_cols, metrics, version)
    logger.success("Training complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train FormulaIQ XGBoost models")
    parser.add_argument("--seasons", type=int, nargs="+", default=[2022, 2023, 2024])
    parser.add_argument("--version", type=str, default="v1")
    args = parser.parse_args()
    run_training(args.seasons, args.version)
