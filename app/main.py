"""
Application entry point.

Creates and configures the FastAPI application, sets up logging,
loads configuration, and registers route handlers.

This module should remain thin — it wires the application together
and starts the server.
"""

import logging

from fastapi import FastAPI

from app.api.routes import router
from app.config.settings import get_settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Loads settings, configures logging, and registers route handlers.
    Called by the ASGI server (uvicorn) to instantiate the application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)

    app = FastAPI(
        title="Candidate Data Transformer",
        description="Multi-source candidate data transformation service",
        version="0.1.0",
    )

    app.include_router(router, prefix="/api/v1")

    logger.info(
        "Application created (host=%s, port=%s, log_level=%s)",
        settings.APP_HOST,
        settings.APP_PORT,
        settings.LOG_LEVEL,
    )

    return app


app = create_app()
