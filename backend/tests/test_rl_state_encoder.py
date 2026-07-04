"""
Tests for rl_strategy/state_encoder.py
Tests that encode_state produces a 15-dim float32 numpy array with correct values.
Pure numpy — no DB, network, or model needed.
"""
import numpy as np
import pytest
from rl_strategy.state_encoder import encode_state


# ── Full valid state fixture ──────────────────────────────────────────────────

FULL_STATE = {
    "current_lap": 20,
    "total_laps": 50,
    "tyre_compound": "Medium",
    "tyre_age": 12,
    "tyre_degradation": 35.0,  # given as %
    "track_temp": 33.5,
    "weather_condition": "dry",
    "safety_car_prob": 0.05,
    "competitor_avg_tyre_age": 10.0,
    "competitor_pit_status": False,
    "current_position": 10,
    "lap_delta_ahead": 1.5,
    "lap_delta_behind": 2.1,
    "fuel_load": 60.0,
    "track_type": "permanent",
}


class TestEncodeState:

    def test_returns_numpy_array(self):
        obs = encode_state(FULL_STATE)
        assert isinstance(obs, np.ndarray)

    def test_observation_is_15_dimensional(self):
        obs = encode_state(FULL_STATE)
        assert obs.shape == (15,), f"Expected shape (15,), got {obs.shape}"

    def test_dtype_is_float32(self):
        obs = encode_state(FULL_STATE)
        assert obs.dtype == np.float32

    def test_current_lap_encoded_correctly(self):
        obs = encode_state(FULL_STATE)
        assert obs[0] == pytest.approx(20.0)

    def test_total_laps_encoded_correctly(self):
        obs = encode_state(FULL_STATE)
        assert obs[1] == pytest.approx(50.0)

    def test_medium_compound_encoded_as_2(self):
        """Medium compound should map to key 2 per COMPOUND_KEYS config."""
        obs = encode_state({**FULL_STATE, "tyre_compound": "Medium"})
        assert obs[2] == pytest.approx(2.0)

    def test_soft_compound_encoded(self):
        """Soft should map to key 1."""
        obs = encode_state({**FULL_STATE, "tyre_compound": "Soft"})
        assert obs[2] == pytest.approx(1.0)

    def test_hard_compound_encoded(self):
        """Hard should map to key 3."""
        obs = encode_state({**FULL_STATE, "tyre_compound": "Hard"})
        assert obs[2] == pytest.approx(3.0)

    def test_tyre_degradation_normalized_from_percentage(self):
        """Degradation given as 35.0 (%) should be normalized to 0.35."""
        obs = encode_state({**FULL_STATE, "tyre_degradation": 35.0})
        assert obs[4] == pytest.approx(0.35, abs=1e-5)

    def test_tyre_degradation_already_normalized_unchanged(self):
        """Degradation given as 0.35 (fraction) should remain 0.35."""
        obs = encode_state({**FULL_STATE, "tyre_degradation": 0.35})
        assert obs[4] == pytest.approx(0.35, abs=1e-5)

    def test_tyre_degradation_clipped_to_1(self):
        """Degradation > 100% should be clipped to 1.0."""
        obs = encode_state({**FULL_STATE, "tyre_degradation": 150.0})
        assert obs[4] == pytest.approx(1.0)

    def test_dry_weather_encoded_as_0(self):
        obs = encode_state({**FULL_STATE, "weather_condition": "dry"})
        assert obs[6] == pytest.approx(0.0)

    def test_wet_weather_encoded_as_1(self):
        obs = encode_state({**FULL_STATE, "weather_condition": "rain"})
        assert obs[6] == pytest.approx(1.0)

    def test_wet_string_alias_works(self):
        obs = encode_state({**FULL_STATE, "weather_condition": "wet"})
        assert obs[6] == pytest.approx(1.0)

    def test_permanent_track_encoded_as_0(self):
        obs = encode_state({**FULL_STATE, "track_type": "permanent"})
        assert obs[14] == pytest.approx(0.0)

    def test_street_track_encoded_as_1(self):
        obs = encode_state({**FULL_STATE, "track_type": "street"})
        assert obs[14] == pytest.approx(1.0)

    def test_competitor_pit_status_false_is_0(self):
        obs = encode_state({**FULL_STATE, "competitor_pit_status": False})
        assert obs[9] == pytest.approx(0.0)

    def test_competitor_pit_status_true_is_1(self):
        obs = encode_state({**FULL_STATE, "competitor_pit_status": True})
        assert obs[9] == pytest.approx(1.0)

    def test_missing_keys_use_defaults(self):
        """encode_state should not crash with an empty dict; defaults fill in."""
        obs = encode_state({})
        assert obs.shape == (15,)
        assert not np.any(np.isnan(obs))

    def test_no_nan_or_inf_values(self):
        obs = encode_state(FULL_STATE)
        assert not np.any(np.isnan(obs))
        assert not np.any(np.isinf(obs))

    def test_numeric_compound_passthrough(self):
        """Integer compound keys should be accepted directly."""
        obs = encode_state({**FULL_STATE, "tyre_compound": 2})
        assert obs[2] == pytest.approx(2.0)

    def test_numeric_weather_passthrough(self):
        """Integer weather code (0=dry, 1=wet) should be accepted directly."""
        obs = encode_state({**FULL_STATE, "weather_condition": 1})
        assert obs[6] == pytest.approx(1.0)
