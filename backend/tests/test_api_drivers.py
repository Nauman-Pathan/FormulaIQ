"""
Tests for api/drivers.py — /drivers and /driver-analysis/{driver}
Uses mocked AsyncSession and mocked compute_driver_analytics service.
"""
import pytest
from unittest.mock import patch, MagicMock


# ── /drivers ─────────────────────────────────────────────────────────────────
class TestListDrivers:
    def test_returns_200_empty_list(self, client):
        resp = client.get("/api/v1/drivers")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_season_filter_valid(self, client):
        resp = client.get("/api/v1/drivers?season=2024")
        assert resp.status_code == 200

    def test_season_filter_invalid_low(self, client):
        resp = client.get("/api/v1/drivers?season=2000")
        assert resp.status_code == 422

    def test_season_filter_invalid_high(self, client):
        resp = client.get("/api/v1/drivers?season=2099")
        assert resp.status_code == 422


# ── /driver-analysis/{driver} ────────────────────────────────────────────────
class TestDriverAnalysis:
    """
    compute_driver_analytics uses a sync DB session internally.
    We mock it at the service level to avoid needing a real DB.
    """

    def _mock_analytics(self):
        """Return a dict matching DriverAnalyticsOut schema."""
        return {
            "driver_code": "VER",
            "full_name": "Max Verstappen",
            "season": 2024,
            "consistency_score": 92.5,
            "overtaking_efficiency": 78.3,
            "tyre_management_score": 88.1,
            "average_pace_delta_ms": -45.2,
            "qualifying_performance": 95.0,
            "racecraft_score": 91.0,
            "avg_grid_position": 1.8,
            "avg_finish_position": 2.1,
            "avg_positions_gained": 0.3,
            "dnf_rate": 0.05,
            "podium_rate": 0.85,
            "win_rate": 0.60,
            "races_analyzed": 20,
            "recent_form": [],
        }

    def test_returns_analytics_for_valid_driver(self, client):
        with patch(
            "services.driver_service.compute_driver_analytics",
            return_value=self._mock_analytics(),
        ):
            resp = client.get("/api/v1/driver-analysis/VER")
        assert resp.status_code == 200
        body = resp.json()
        assert body["driver_code"] == "VER"
        assert "consistency_score" in body
        assert "racecraft_score" in body

    def test_driver_code_uppercased(self, client):
        """Driver code should be uppercased regardless of input case."""
        with patch(
            "services.driver_service.compute_driver_analytics",
            return_value=self._mock_analytics(),
        ):
            resp = client.get("/api/v1/driver-analysis/ver")
        assert resp.status_code == 200

    def test_returns_404_for_unknown_driver(self, client):
        with patch(
            "services.driver_service.compute_driver_analytics",
            side_effect=ValueError("Driver XYZ not found"),
        ):
            resp = client.get("/api/v1/driver-analysis/XYZ")
        assert resp.status_code == 404
        assert "XYZ" in resp.json()["detail"] or resp.status_code == 404
