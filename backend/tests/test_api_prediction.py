"""
Tests for api/prediction.py — POST /predict-race
Mocks ml.predict.predict_race so no real model file is needed.
"""
import pytest
from unittest.mock import patch


# ── Helpers ──────────────────────────────────────────────────────────────────
VALID_DRIVER = {
    "driver_code": "VER",
    "driver_name": "Max Verstappen",
    "constructor": "Red Bull",
    "grid_position": 1,
    "best_qualifying_time_seconds": 83.778,
    "consistency_score": 92.0,
    "avg_lap_time": 91.5,
    "prev3_avg_finish": 1.7,
    "cumulative_points": 275.0,
    "num_pit_stops": 2,
    "avg_pit_duration": 23.5,
    "weather_code": 0,
    "rainfall": 0,
    "air_temp_avg": 28.0,
    "track_temp_avg": 42.0,
    "humidity_avg": 45.0,
    "grid_delta": 0,
    "laps_completed": 52.0,
}

VALID_DRIVER_2 = {**VALID_DRIVER, "driver_code": "NOR", "grid_position": 2, "cumulative_points": 240.0}

MOCK_PREDICTION_RESPONSE = {
    "race_id": None,
    "year": 2024,
    "grand_prix": "Test GP",
    "model_version": "v1",
    "predictions": [
        {
            "driver_code": "VER",
            "driver_name": "Max Verstappen",
            "constructor": "Red Bull",
            "predicted_position": 1.2,
            "predicted_position_int": 1,
            "win_probability": 0.65,
            "podium_probability": 0.90,
            "top10_probability": 0.99,
            "dnf_probability": 0.03,
        }
    ],
    "feature_importances": {"grid_position": 0.35, "prev3_avg_finish": 0.25},
}


class TestPredictRace:
    def test_valid_request_returns_200(self, client):
        with patch("ml.predict.predict_race", return_value=MOCK_PREDICTION_RESPONSE):
            resp = client.post(
                "/api/v1/predict-race",
                json={
                    "year": 2024,
                    "grand_prix": "Test GP",
                    "model_version": "v1",
                    "drivers": [VALID_DRIVER, VALID_DRIVER_2],
                },
            )
        assert resp.status_code == 200

    def test_response_has_predictions_list(self, client):
        with patch("ml.predict.predict_race", return_value=MOCK_PREDICTION_RESPONSE):
            resp = client.post(
                "/api/v1/predict-race",
                json={
                    "year": 2024,
                    "grand_prix": "Test GP",
                    "model_version": "v1",
                    "drivers": [VALID_DRIVER, VALID_DRIVER_2],
                },
            )
        body = resp.json()
        assert "predictions" in body
        assert isinstance(body["predictions"], list)

    def test_driver_code_uppercased(self, client):
        """driver_code 'ver' should be stored/sent as 'VER'."""
        driver = {**VALID_DRIVER, "driver_code": "ver"}
        with patch("ml.predict.predict_race", return_value=MOCK_PREDICTION_RESPONSE):
            resp = client.post(
                "/api/v1/predict-race",
                json={"drivers": [driver, VALID_DRIVER_2]},
            )
        # Schema validator uppercases; request should be accepted
        assert resp.status_code == 200

    def test_too_few_drivers_rejected(self, client):
        """Fewer than 2 drivers should fail schema validation (422)."""
        resp = client.post(
            "/api/v1/predict-race",
            json={"drivers": [VALID_DRIVER]},
        )
        assert resp.status_code == 422

    def test_too_many_drivers_rejected(self, client):
        """More than 20 drivers should fail schema validation (422)."""
        drivers = [{**VALID_DRIVER, "driver_code": f"D{i:02d}", "grid_position": i + 1} for i in range(21)]
        resp = client.post(
            "/api/v1/predict-race",
            json={"drivers": drivers},
        )
        assert resp.status_code == 422

    def test_invalid_grid_position_rejected(self, client):
        """grid_position must be 1–20."""
        driver = {**VALID_DRIVER, "grid_position": 25}
        resp = client.post(
            "/api/v1/predict-race",
            json={"drivers": [driver, VALID_DRIVER_2]},
        )
        assert resp.status_code == 422

    def test_negative_qualifying_time_rejected(self, client):
        """best_qualifying_time_seconds must be > 0."""
        driver = {**VALID_DRIVER, "best_qualifying_time_seconds": -1.0}
        resp = client.post(
            "/api/v1/predict-race",
            json={"drivers": [driver, VALID_DRIVER_2]},
        )
        assert resp.status_code == 422
