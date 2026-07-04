"""
Tests for api/strategy.py — POST /simulate-strategy
Also tests the underlying strategy_service logic directly (no HTTP layer).
"""
import pytest
from services.strategy_service import simulate_strategy, _degrade_lap_time, _optimal_pit_lap
from models.schemas import StrategySimRequest


# ── Helpers ──────────────────────────────────────────────────────────────────
def make_request(**kwargs) -> StrategySimRequest:
    defaults = {
        "current_lap": 20,
        "total_laps": 50,
        "tyre_compound": "MEDIUM",
        "tyre_age_laps": 15,
        "current_position": 5,
        "weather_condition": "dry",
        "safety_car_probability": 0.15,
        "pit_lane_loss_seconds": 22.0,
        "degradation_rate": 0.08,
        "circuit_type": "permanent",
    }
    defaults.update(kwargs)
    return StrategySimRequest(**defaults)


# ── HTTP endpoint tests ───────────────────────────────────────────────────────
class TestStrategyEndpoint:
    def test_valid_request_returns_200(self, client):
        payload = {
            "current_lap": 20,
            "total_laps": 50,
            "tyre_compound": "MEDIUM",
            "tyre_age_laps": 15,
            "current_position": 5,
            "weather_condition": "dry",
            "safety_car_probability": 0.15,
            "pit_lane_loss_seconds": 22.0,
            "degradation_rate": 0.08,
            "circuit_type": "permanent",
        }
        resp = client.post("/api/v1/simulate-strategy", json=payload)
        assert resp.status_code == 200

    def test_response_has_required_keys(self, client):
        payload = {
            "current_lap": 20,
            "total_laps": 50,
            "tyre_compound": "SOFT",
            "tyre_age_laps": 18,
            "current_position": 3,
            "weather_condition": "dry",
            "safety_car_probability": 0.10,
            "pit_lane_loss_seconds": 20.0,
            "degradation_rate": 0.10,
            "circuit_type": "street",
        }
        resp = client.post("/api/v1/simulate-strategy", json=payload)
        body = resp.json()
        assert "recommended_strategy" in body
        assert "all_strategies" in body
        assert "current_tyre_degradation_pct" in body
        assert "laps_to_pit_window_open" in body
        assert "laps_to_pit_window_close" in body
        assert "notes" in body

    def test_invalid_compound_rejected(self, client):
        payload = {
            "current_lap": 20,
            "total_laps": 50,
            "tyre_compound": "SUPERSOFT",  # invalid
            "tyre_age_laps": 10,
            "current_position": 5,
        }
        resp = client.post("/api/v1/simulate-strategy", json=payload)
        assert resp.status_code == 422

    def test_invalid_weather_rejected(self, client):
        payload = {
            "current_lap": 20,
            "total_laps": 50,
            "tyre_compound": "MEDIUM",
            "tyre_age_laps": 10,
            "current_position": 5,
            "weather_condition": "SUNNY",  # invalid
        }
        resp = client.post("/api/v1/simulate-strategy", json=payload)
        assert resp.status_code == 422


# ── Service unit tests (no HTTP layer) ───────────────────────────────────────
class TestStrategyService:
    def test_simulate_strategy_returns_dict(self):
        req = make_request()
        result = simulate_strategy(req)
        assert isinstance(result, dict)
        assert result["recommended_strategy"] is not None

    def test_all_strategies_non_empty(self):
        req = make_request()
        result = simulate_strategy(req)
        assert len(result["all_strategies"]) > 0

    def test_all_strategies_capped_at_6(self):
        req = make_request()
        result = simulate_strategy(req)
        assert len(result["all_strategies"]) <= 6

    def test_degradation_pct_between_0_and_100(self):
        req = make_request()
        result = simulate_strategy(req)
        pct = result["current_tyre_degradation_pct"]
        assert 0.0 <= pct <= 100.0

    def test_soft_tyre_degrades_faster_than_hard(self):
        """Soft lap time past its cliff (age=40>22) should be worse than Hard at same age."""
        soft_time = _degrade_lap_time(90.0, "SOFT", 40, 0.08)
        hard_time = _degrade_lap_time(90.0, "HARD", 40, 0.08)
        assert soft_time > hard_time

    def test_optimal_pit_lap_within_race_bounds(self):
        req = make_request()
        optimal = _optimal_pit_lap(req)
        assert req.current_lap < optimal < req.total_laps

    def test_wet_conditions_notes_mention_weather(self):
        req = make_request(weather_condition="wet")
        result = simulate_strategy(req)
        assert "wet" in result["notes"].lower() or "🌧️" in result["notes"]

    def test_high_sc_probability_notes_mention_safety_car(self):
        req = make_request(safety_car_probability=0.5)
        result = simulate_strategy(req)
        assert "SC" in result["notes"] or "safety" in result["notes"].lower() or "🚗" in result["notes"]
