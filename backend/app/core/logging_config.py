"""
Structured logging configuration.
Sets up JSON-style logging in production and human-readable logging in dev.
"""
import logging
import sys

from app.core.config import get_settings

settings = get_settings()


def setup_logging() -> None:
    """
    Configure application-wide logging.
    Call this once at application startup in main.py.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Root logger format
    if settings.environment == "production":
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    else:
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    logging.basicConfig(
        level=log_level,
        format=fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.environment == "development" else logging.WARNING
    )
    logging.getLogger("passlib").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured | level=%s | env=%s",
        settings.log_level,
        settings.environment,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Returns a named logger.
    Usage:
        logger = get_logger(__name__)
        logger.info("Something happened")
    """
    return logging.getLogger(name)
