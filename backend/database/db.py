"""
FormulaIQ — Database Engine & Session Factory
Uses psycopg v3 (works with Python 3.14).
Provides both sync and async session makers.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# ── Sync Engine ────────────────────────────────────────────────────────────
# psycopg v3 sync: postgresql+psycopg://
sync_engine = create_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=not settings.is_production,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# ── Async Engine ───────────────────────────────────────────────────────────
# psycopg v3 async: postgresql+psycopg_async://
async_engine = create_async_engine(
    settings.DATABASE_URL_ASYNC,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=not settings.is_production,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ── Declarative Base ────────────────────────────────────────────────────────
Base = declarative_base()


# ── Dependency Injectors ────────────────────────────────────────────────────
def get_sync_db():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
