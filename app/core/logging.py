"""
Logging configuration for the application.

Provides a single entry point to configure structured logging
across all modules. Uses the standard library logging module
with a consistent format that includes timestamps, log levels,
and module names.
"""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """
    Configure the root logger for the application.

    Sets up a console handler with a structured format that captures
    timestamp, log level, module name, and message. Respects the
    configured log level from application settings.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR).
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    # Silence overly verbose third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger.debug("Logging configured at %s level", level)
