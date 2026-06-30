"""
Abstract client interface for AI-powered extraction.

All AI client implementations (Gemini, OpenAI, HuggingFace, etc.)
inherit from this base. Parsers depend on the abstraction, never
on a concrete client.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class AiClient(ABC):
    """
    Abstract interface for AI model interactions.

    Implementations handle sending text content with an extraction
    prompt and returning structured JSON. This interface allows
    parsers to depend on an abstraction rather than a concrete HTTP
    client, enabling testability through dependency injection.
    """

    @abstractmethod
    def extract(self, text: str, prompt: str) -> dict[str, Any]:
        """
        Send text content to the AI and return structured extraction.

        Args:
            text: Raw text content to extract information from.
            prompt: Instruction prompt describing the extraction schema.

        Returns:
            Structured dictionary matching the extraction schema.

        Raises:
            ConnectionError: If the AI API is unreachable.
            ValueError: If the response cannot be parsed.
        """
        ...
