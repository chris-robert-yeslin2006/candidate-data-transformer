"""
API route definitions.

This module is intentionally minimal. Routes delegate all business
logic to PipelineService. No business logic lives in route handlers.
"""

import logging

from fastapi import APIRouter

from app import __version__

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns service status, version, and name.
    TODO: Add dependency health checks (Gemini API reachability, etc.).
    """
    logger.debug("Health check requested")
    return {
        "status": "healthy",
        "version": __version__,
        "service": "candidate-transformer",
    }
