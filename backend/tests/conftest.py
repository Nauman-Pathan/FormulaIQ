"""
FormulaIQ — Shared pytest fixtures.

Mocks:
- AsyncSession (database) so no live DB is needed
- Redis cache (cache_get / cache_set always return None / True)
- ML model (predict_race) so no joblib file is needed
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# ── Patch Redis cache layer before app import ────────────────────────────────
@pytest.fixture(autouse=True)
def mock_cache(monkeypatch):
    """Make cache_get always miss and cache_set always succeed (no Redis needed)."""
    async def _cache_get(_key):
        return None

    async def _cache_set(_key, _value, ttl=None):
        return True

    monkeypatch.setattr("utils.cache.cache_get", _cache_get)
    monkeypatch.setattr("utils.cache.cache_set", _cache_set)


# ── Async DB session mock ────────────────────────────────────────────────────
@pytest.fixture()
def mock_async_db():
    """Return a mock AsyncSession that returns empty scalars by default."""
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    result.all.return_value = []
    session.execute.return_value = result
    return session


# ── TestClient (lazy import avoids circular issues) ─────────────────────────
@pytest.fixture()
def client(mock_async_db):
    """
    Build a TestClient with the async DB dependency overridden.
    The ML predict endpoint also needs the model mocked.
    """
    from main import app
    from database.db import get_async_db

    async def _override_db():
        yield mock_async_db

    app.dependency_overrides[get_async_db] = _override_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
