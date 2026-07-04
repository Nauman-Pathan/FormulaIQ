"""
Tests for ml/feature_engineering.py
Tests that build_feature_matrix produces correct shape, columns, and fills NaNs.
No DB or network access needed — pure pandas/numpy.
"""
import numpy as np
import pandas as pd
import pytest

from ml.feature_engineering import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    build_feature_matrix,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def make_race_results(n: int = 4) -> pd.DataFrame:
    """Minimal race_results dataframe (required input)."""
    return pd.DataFrame(
        {
            "race_id": [1] * n,
            "driver_id": list(range(1, n + 1)),
            "grid_position": list(range(1, n + 1)),
            "finish_position": list(range(1, n + 1)),
            "points_scored": [25, 18, 15, 12][:n],
            "dnf": [False] * n,
            "season": [2024] * n,
        }
    )


def make_qualifying(n: int = 4) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "race_id": [1] * n,
            "driver_id": list(range(1, n + 1)),
            "best_qualifying_time_seconds": [83.0, 83.2, 83.5, 83.8][:n],
            "grid_position": list(range(1, n + 1)),
        }
    )


def make_lap_times(n: int = 4) -> pd.DataFrame:
    rows = []
    for drv in range(1, n + 1):
        for lap in range(1, 11):
            rows.append(
                {
                    "race_id": 1,
                    "driver_id": drv,
                    "lap_number": lap,
                    "lap_time_seconds": 90.0 + drv * 0.1 + lap * 0.05,
                    "sector1_seconds": 28.0,
                    "sector2_seconds": 32.0,
                    "sector3_seconds": 30.0,
                }
            )
    return pd.DataFrame(rows)


def make_pit_stops(n: int = 4) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "race_id": [1] * n,
            "driver_id": list(range(1, n + 1)),
            "stop_number": [2] * n,
            "pit_duration_seconds": [22.5, 23.0, 24.1, 21.8][:n],
        }
    )


def make_weather() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "race_id": [1],
            "air_temp_avg": [28.0],
            "track_temp_avg": [42.0],
            "humidity_avg": [50.0],
            "rainfall": [0],
            "condition": ["dry"],
        }
    )


EMPTY = pd.DataFrame()


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestBuildFeatureMatrix:

    def test_returns_empty_dataframe_when_no_results(self):
        result = build_feature_matrix(EMPTY, EMPTY, EMPTY, EMPTY, EMPTY)
        assert result.empty

    def test_returns_dataframe_with_correct_number_of_rows(self):
        rr = make_race_results(4)
        result = build_feature_matrix(rr, EMPTY, EMPTY, EMPTY, EMPTY)
        assert len(result) == 4

    def test_all_feature_columns_present(self):
        rr = make_race_results(4)
        q = make_qualifying(4)
        lt = make_lap_times(4)
        ps = make_pit_stops(4)
        w = make_weather()
        result = build_feature_matrix(rr, q, lt, ps, w)
        missing = [col for col in FEATURE_COLUMNS if col not in result.columns]
        assert missing == [], f"Missing feature columns: {missing}"

    def test_target_column_present(self):
        rr = make_race_results(4)
        result = build_feature_matrix(rr, EMPTY, EMPTY, EMPTY, EMPTY)
        assert TARGET_COLUMN in result.columns

    def test_no_nans_in_key_features_after_fill(self):
        """After build_feature_matrix, key columns should have no NaN values."""
        rr = make_race_results(4)
        q = make_qualifying(4)
        lt = make_lap_times(4)
        ps = make_pit_stops(4)
        w = make_weather()
        result = build_feature_matrix(rr, q, lt, ps, w)
        for col in ["consistency_score", "num_pit_stops", "avg_pit_duration",
                    "weather_code", "rainfall"]:
            if col in result.columns:
                assert result[col].isna().sum() == 0, f"NaN found in column: {col}"

    def test_weather_code_is_0_for_dry(self):
        rr = make_race_results(2)
        w = make_weather()
        result = build_feature_matrix(rr, EMPTY, EMPTY, EMPTY, w)
        assert (result["weather_code"] == 0).all()

    def test_consistency_score_computed_correctly(self):
        """Consistency score = 1 / (std/mean + eps). Should be > 0 for valid lap times."""
        rr = make_race_results(4)
        lt = make_lap_times(4)
        result = build_feature_matrix(rr, EMPTY, lt, EMPTY, EMPTY)
        if "consistency_score" in result.columns:
            valid = result["consistency_score"].dropna()
            assert (valid > 0).all()

    def test_cumulative_points_non_negative(self):
        """Cumulative season points should always be >= 0."""
        rr = make_race_results(4)
        result = build_feature_matrix(rr, EMPTY, EMPTY, EMPTY, EMPTY)
        assert (result["cumulative_points"] >= 0).all()

    def test_feature_columns_list_has_expected_length(self):
        """FEATURE_COLUMNS must have exactly 15 entries to match RL obs space."""
        assert len(FEATURE_COLUMNS) == 15

    def test_full_pipeline_produces_expected_shape(self):
        """Full pipeline with all inputs: shape should be (n_drivers, >= len(FEATURE_COLUMNS))."""
        rr = make_race_results(4)
        q = make_qualifying(4)
        lt = make_lap_times(4)
        ps = make_pit_stops(4)
        w = make_weather()
        result = build_feature_matrix(rr, q, lt, ps, w)
        assert result.shape[0] == 4
        assert result.shape[1] >= len(FEATURE_COLUMNS)
