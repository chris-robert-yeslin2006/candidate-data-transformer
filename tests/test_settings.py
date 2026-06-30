"""
Application settings tests.

Verifies that settings load correctly from environment variables
and provide sensible defaults.
"""

import pytest

from app.config.settings import Settings


def test_settings_defaults() -> None:
    """Settings should provide sensible defaults for all fields."""
    settings = Settings()
    assert settings.APP_HOST == "0.0.0.0"
    assert settings.APP_PORT == 8000
    assert settings.LOG_LEVEL == "INFO"
    assert settings.GEMINI_MODEL == "gemini-2.0-flash"


def test_settings_custom_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should honour environment variable overrides."""
    monkeypatch.setenv("APP_PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")

    settings = Settings()
    assert settings.APP_PORT == 9000
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.GEMINI_API_KEY == "test-key-123"
