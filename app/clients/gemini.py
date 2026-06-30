"""
Gemini API client implementation.

Provides a concrete AiClient implementation backed by the Google
Gemini API. Also includes a MockGeminiClient for deterministic
testing without network access.
"""

import logging
from typing import Any

from app.clients.base import AiClient

logger = logging.getLogger(__name__)


class GeminiClient(AiClient):
    """
    Gemini-specific AI client.

    Uses the google-genai SDK to call Gemini models. Reads the API
    key from application settings. Should be injected via dependency
    injection, not instantiated directly.

    TODO: Implement actual API call logic.
    """

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        """
        Initialize the Gemini client.

        Args:
            api_key: Google Gemini API key.
            model: Gemini model identifier.
        """
        self._api_key = api_key
        self._model = model
        logger.info("GeminiClient initialized with model: %s", model)

    def extract(self, text: str, prompt: str) -> dict[str, Any]:
        """
        Send text to Gemini and return structured extraction.

        Args:
            text: Raw text content to extract from.
            prompt: Extraction instruction prompt.

        Returns:
            Structured extraction result as a dictionary.

        Raises:
            NotImplementedError: Until the actual API integration is implemented.
        """
        # TODO: Implement Gemini API call
        logger.warning("GeminiClient.extract is not yet implemented")
        raise NotImplementedError("Gemini API integration is not yet implemented")


class MockGeminiClient(AiClient):
    """
    Mock AI client for unit testing.

    Returns deterministic JSON fixtures instead of calling the API.
    Allows parsers to be tested without network access or API keys.
    """

    def __init__(self, fixture: dict[str, Any] | None = None) -> None:
        """
        Initialize the mock client.

        Args:
            fixture: Optional deterministic response to return.
                     If None, returns a minimal empty extraction.
        """
        self._fixture = fixture or {
            "name": "",
            "phone": "",
            "email": "",
            "skills": [],
            "experience": [],
            "education": [],
        }
        logger.debug("MockGeminiClient initialized")

    def extract(self, text: str, prompt: str) -> dict[str, Any]:
        """
        Return the configured fixture regardless of input.

        Args:
            text: Ignored in mock implementation.
            prompt: Ignored in mock implementation.

        Returns:
            Pre-configured deterministic fixture dictionary.
        """
        logger.debug("MockGeminiClient.extract called (returning fixture)")
        return self._fixture.copy()
