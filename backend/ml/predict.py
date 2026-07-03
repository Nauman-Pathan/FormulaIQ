"""
FormulaIQ — Race Prediction Inference Engine (Module 3)
Loads trained XGBoost models and produces per-driver probability scores.
"""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from ml.feature_engineering import FEATURE_COLUMNS

MODEL_DIR = Path(settings.MODEL_DIR)
_position_model = None
_dnf_model = None
_metadata: Dict[str, Any] = {}


def load_models(version: str = "v1"):
    """Load model artifacts from disk (cached in module globals)."""
    global _position_model, _dnf_model, _metadata

    pos_path = MODEL_DIR / f"position_model_{version}.joblib"
    dnf_path = MODEL_DIR / f"dnf_model_{version}.joblib"
    meta_path = MODEL_DIR / f"model_metadata_{version}.json"

    if not pos_path.exists():
        raise FileNotFoundError(f"No trained model found at {pos_path}. Run train_model.py first.")

    _position_model = joblib.load(pos_path)
    _dnf_model = joblib.load(dnf_path)

    with open(meta_path) as f:
        _metadata = json.load(f)

    logger.info("Models loaded | version={}", version)


def _ensure_models_loaded(version: str = "v1"):
    if _position_model is None:
        load_models(version)


def predict_race(driver_inputs: List[Dict[str, Any]], version: str = "v1") -> List[Dict[str, Any]]:
    """
    Predict finishing positions and probabilities for a list of drivers.

    Args:
        driver_inputs: List of feature dicts, one per driver.
            Required keys: grid_position, best_qualifying_time_seconds,
            consistency_score, avg_lap_time, prev3_avg_finish,
            cumulative_points, num_pit_stops, avg_pit_duration,
            weather_code, rainfall, air_temp_avg, track_temp_avg,
            humidity_avg, grid_delta, laps_completed

    Returns:
        List of predictions sorted by predicted_position.
    """
    _ensure_models_loaded(version)

    feature_cols = _metadata.get("feature_columns", FEATURE_COLUMNS)

    # Build feature matrix
    rows = []
    for d in driver_inputs:
        row = [d.get(col, 0.0) or 0.0 for col in feature_cols]
        rows.append(row)

    X = np.array(rows, dtype=float)

    # Predictions
    predicted_positions = _position_model.predict(X)
    dnf_probabilities = _dnf_model.predict_proba(X)[:, 1]

    results = []
    for i, driver in enumerate(driver_inputs):
        raw_pos = float(predicted_positions[i])
        clipped_pos = max(1.0, min(raw_pos, 20.0))
        dnf_prob = float(dnf_probabilities[i])

        # Derive tier probabilities from position distribution
        win_prob = _position_to_prob(clipped_pos, threshold=1.5)
        podium_prob = _position_to_prob(clipped_pos, threshold=3.5)
        top10_prob = _position_to_prob(clipped_pos, threshold=10.5)

        results.append({
            "driver_code": driver.get("driver_code", f"DRV{i+1}"),
            "driver_name": driver.get("driver_name", ""),
            "constructor": driver.get("constructor", ""),
            "predicted_position": round(clipped_pos, 1),
            "predicted_position_int": round(clipped_pos),
            "win_probability": round(win_prob * (1 - dnf_prob), 4),
            "podium_probability": round(podium_prob * (1 - dnf_prob), 4),
            "top10_probability": round(top10_prob * (1 - dnf_prob), 4),
            "dnf_probability": round(dnf_prob, 4),
        })

    # Sort by predicted position
    results.sort(key=lambda r: r["predicted_position"])

    # Normalize win probabilities to sum to 1
    total_win = sum(r["win_probability"] for r in results) or 1.0
    for r in results:
        r["win_probability"] = round(r["win_probability"] / total_win, 4)

    logger.info("Race prediction complete | {} drivers", len(results))
    return results


def _position_to_prob(position: float, threshold: float) -> float:
    """Sigmoid-based probability from predicted position vs threshold."""
    diff = threshold - position
    return float(1.0 / (1.0 + np.exp(-2.0 * diff)))


def get_feature_importances(version: str = "v1") -> Dict[str, float]:
    """Return feature importances from the trained model."""
    _ensure_models_loaded(version)
    return _metadata.get("feature_importances", {})


def get_model_metadata(version: str = "v1") -> Dict[str, Any]:
    """Return model metadata including metrics."""
    _ensure_models_loaded(version)
    return _metadata
