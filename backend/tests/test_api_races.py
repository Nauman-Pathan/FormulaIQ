"""
Tests for api/races.py — /races, /races/{id}/results, /circuits, /historical-results
Uses mocked AsyncSession so no live DB is needed.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


# ── /races ───────────────────────────────────────────────────────────────────
class TestListRaces:
    def test_returns_200_empty_list(self, client):
        """When DB returns no rows, endpoint returns 200 with empty list."""
        resp = client.get("/api/v1/races")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_season_filter_accepted(self, client):
        """Season query param in valid range (2022-2026) is accepted."""
        resp = client.get("/api/v1/races?season=2024")
        assert resp.status_code == 200

    def test_season_below_range_rejected(self, client):
        """Season below 2022 should fail validation (422)."""
        resp = client.get("/api/v1/races?season=2010")
        assert resp.status_code == 422

    def test_season_above_range_rejected(self, client):
        """Season above 2026 should fail validation (422)."""
        resp = client.get("/api/v1/races?season=2030")
        assert resp.status_code == 422


# ── /races/{race_id}/results ─────────────────────────────────────────────────
class TestGetRaceResults:
    def test_returns_404_when_no_results(self, client):
        """If DB returns no rows, endpoint should return 404."""
        resp = client.get("/api/v1/races/999/results")
        assert resp.status_code == 404
        assert "No results" in resp.json()["detail"]

    def test_invalid_race_id_type_rejected(self, client):
        """Non-integer race_id should return 422."""
        resp = client.get("/api/v1/races/abc/results")
        assert resp.status_code == 422


# ── /circuits ────────────────────────────────────────────────────────────────
class TestListCircuits:
    def test_returns_200_empty_list(self, client):
        """When DB returns no rows, endpoint returns 200 with empty list."""
        resp = client.get("/api/v1/circuits")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ── /historical-results ──────────────────────────────────────────────────────
class TestHistoricalResults:
    def test_returns_200_no_filters(self, client):
        resp = client.get("/api/v1/historical-results")
        assert resp.status_code == 200

    def test_limit_param_accepted(self, client):
        resp = client.get("/api/v1/historical-results?limit=10")
        assert resp.status_code == 200

    def test_limit_too_large_rejected(self, client):
        resp = client.get("/api/v1/historical-results?limit=999")
        assert resp.status_code == 422

    def test_driver_code_filter_accepted(self, client):
        resp = client.get("/api/v1/historical-results?driver_code=VER")
        assert resp.status_code == 200

    def test_season_filter_accepted(self, client):
        resp = client.get("/api/v1/historical-results?season=2024")
        assert resp.status_code == 200
