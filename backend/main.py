"""
FormulaIQ — FastAPI Application Entry Point
Wires all routers, middleware, exception handlers, and lifecycle events.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import settings
from app.logging import setup_logging
from api.telemetry import router as telemetry_router
from api.prediction import router as prediction_router
from api.strategy import router as strategy_router
from api.races import router as races_router
from api.drivers import router as drivers_router
from api.rl_strategy import router as rl_strategy_router


# ── Lifecycle ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle handler."""
    setup_logging()
    logger.info("FormulaIQ API starting | env={}", settings.APP_ENV)
    yield
    logger.info("FormulaIQ API shutting down")


# ── App Factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="FormulaIQ API",
    description=(
        "🏎️ **FormulaIQ** — AI-powered Formula 1 analytics platform.\n\n"
        "Provides race outcome predictions, telemetry comparison, "
        "strategy simulation, and driver analytics powered by FastF1 + XGBoost."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception Handlers ────────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception | path={} err={}", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": str(request.url.path)},
    )

# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(races_router, prefix=API_PREFIX)
app.include_router(drivers_router, prefix=API_PREFIX)
app.include_router(telemetry_router, prefix=API_PREFIX)
app.include_router(prediction_router, prefix=API_PREFIX)
app.include_router(strategy_router, prefix=API_PREFIX)
app.include_router(rl_strategy_router, prefix=API_PREFIX)

# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0", "service": "FormulaIQ API"}


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "🏎️ FormulaIQ API",
        "docs": "/docs",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.API_WORKERS,
        reload=not settings.is_production,
    )
