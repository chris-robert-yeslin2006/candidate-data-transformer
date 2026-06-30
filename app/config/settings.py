"""
Application settings loaded from environment variables.

Uses pydantic-settings to validate and load configuration at startup.
All secrets (API keys) are injected via environment variables and never
hard-coded.
"""

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application configuration container.

    Loads values from environment variables and .env file with
    Pydantic validation. All fields have sensible defaults where
    appropriate; secrets require explicit configuration.

    Attributes:
        GEMINI_API_KEY: API key for Google Gemini.
        GEMINI_MODEL: Model identifier for Gemini API calls.
        APP_HOST: Host address for the FastAPI server.
        APP_PORT: Port for the FastAPI server.
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Gemini configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # Application configuration
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Using lru_cache ensures settings are loaded once and reused
    across the application lifetime, avoiding repeated file I/O.

    Returns:
        Application Settings instance.
    """
    logger.debug("Loading application settings")
    return Settings()
