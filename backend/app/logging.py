"""
FormulaIQ Backend — Structured Logging Setup
Uses loguru for rich, structured logging with file rotation.
"""
import sys
from pathlib import Path
from loguru import logger
from app.config import settings


def setup_logging() -> None:
    """Configure loguru with console + rotating file handlers."""
    # Remove default handler
    logger.remove()

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
    )

    # File handler with rotation
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        settings.LOG_FILE,
        format=log_format,
        level=settings.LOG_LEVEL,
        rotation="50 MB",
        retention="30 days",
        compression="gz",
        enqueue=True,  # thread-safe async logging
    )

    logger.info("Logging initialized | env={}", settings.APP_ENV)
