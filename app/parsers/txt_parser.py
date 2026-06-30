"""
Plain-text notes parser.

Uses Gemini AI to extract structured candidate information from
free-form recruiter notes or plain-text candidate profiles.

TODO: Implement Gemini-based extraction in Phase 8.
"""

from __future__ import annotations

import logging
from typing import Any

from app.clients.base import AiClient
from app.domain.models import CanonicalCandidate
from app.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class TxtNotesParser(BaseParser):
    """
    Parser for plain-text candidate notes.

    Sends free-form text content to Gemini for semantic extraction of
    candidate fields. Designed for recruiter notes, interview summaries,
    and other unstructured text inputs.

    Depends on an AiClient abstraction for AI extraction, enabling
    unit testing with MockGeminiClient.

    TODO: Implement Gemini extraction call.
    TODO: Handle extraction failures gracefully (return partial data).
    """

    def __init__(self, ai_client: AiClient) -> None:
        """
        Initialize the text notes parser.

        Args:
            ai_client: AiClient instance for AI extraction.
        """
        self._ai_client = ai_client
        logger.debug("TxtNotesParser initialized")

    def parse(self, raw_data: str | bytes, **kwargs: Any) -> CanonicalCandidate:
        """
        Parse plain-text notes into a CanonicalCandidate.

        Args:
            raw_data: Plain-text content as a string.
            **kwargs: Optional extraction parameters.

        Returns:
            CanonicalCandidate with parsed fields.

        Raises:
            ParsingError: If text extraction fails.
        """
        # TODO: Implement TXT parsing
        logger.warning("TxtNotesParser.parse is not yet implemented")
        raise NotImplementedError("Text notes parsing is not yet implemented")
