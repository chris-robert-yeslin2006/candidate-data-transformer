"""
Gemini API client implementation.

Provides a concrete AiClient implementation backed by the Google
Gemini API. Also includes a MockGeminiClient for deterministic
testing without network access.
"""

import json
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
        self._client = None
        logger.info("GeminiClient initialized with model: %s", model)

    def _get_client(self) -> Any:
        """
        Lazily initialize the Gemini client.

        Returns:
            Configured google.genai.Client instance.
        """
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self._api_key)
            except ImportError:
                logger.error("google-genai package is not installed")
                raise
            except Exception as exc:
                logger.error("Failed to initialize Gemini client: %s", exc)
                raise ConnectionError(f"Gemini client initialization failed: {exc}")
        return self._client

    def extract(self, text: str, prompt: str) -> dict[str, Any]:
        """
        Send text to Gemini and return structured extraction.

        Args:
            text: Raw text content to extract from.
            prompt: Extraction instruction prompt.

        Returns:
            Structured extraction result as a dictionary.

        Raises:
            ConnectionError: If the Gemini API is unreachable.
            ValueError: If the response cannot be parsed as JSON.
        """
        client = self._get_client()

        full_prompt = f"{prompt}\n\n---\n\nContent to extract from:\n\n{text}"

        try:
            response = client.models.generate_content(
                model=self._model,
                contents=full_prompt,
            )

            response_text = response.text or ""

            # Strip markdown code fences if present
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            result = json.loads(response_text)
            if not isinstance(result, dict):
                raise ValueError(f"Expected JSON object, got {type(result).__name__}")

            return result

        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Gemini response as JSON: %s", exc)
            raise ValueError(f"Gemini response is not valid JSON: {exc}")
        except Exception as exc:
            if isinstance(exc, (ValueError, ConnectionError)):
                raise
            logger.error("Gemini API call failed: %s", exc)
            raise ConnectionError(f"Gemini API error: {exc}")


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
