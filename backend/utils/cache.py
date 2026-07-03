"""
FormulaIQ — Redis Caching Utility
Gracefully falls back to no-op when Redis is unavailable.
"""
import json
from typing import Any, Optional

from loguru import logger

from app.config import settings

_redis_pool = None
_redis_available = None  # None = not yet tested


async def _get_redis():
    """Get or create Redis connection. Returns None if unavailable."""
    global _redis_pool, _redis_available

    if _redis_available is False:
        return None

    if _redis_pool is not None:
        return _redis_pool

    try:
        import redis.asyncio as aioredis
        pool = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=1,
        )
        await pool.ping()
        _redis_pool = pool
        _redis_available = True
        logger.info("Redis connected at {}", settings.REDIS_URL)
        return pool
    except Exception as exc:
        _redis_available = False
        logger.warning("Redis unavailable — running without cache ({})", exc)
        return None


async def cache_get(key: str) -> Optional[Any]:
    try:
        redis = await _get_redis()
        if redis is None:
            return None
        value = await redis.get(key)
        if value:
            logger.debug("Cache HIT | key={}", key)
            return json.loads(value)
        return None
    except Exception as exc:
        logger.debug("Cache GET failed | {}", exc)
        return None


async def cache_set(key: str, value: Any, ttl: int = settings.CACHE_TTL) -> bool:
    try:
        redis = await _get_redis()
        if redis is None:
            return False
        await redis.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as exc:
        logger.debug("Cache SET failed | {}", exc)
        return False


async def cache_delete(pattern: str) -> int:
    try:
        redis = await _get_redis()
        if redis is None:
            return 0
        keys = await redis.keys(pattern)
        if keys:
            return await redis.delete(*keys)
        return 0
    except Exception:
        return 0


def make_cache_key(*parts: Any) -> str:
    return "formulaiq:" + ":".join(str(p).lower().replace(" ", "_") for p in parts)
