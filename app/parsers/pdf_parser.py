"""
PDF resume parser.

Extracts text from PDF documents and uses Gemini AI to semantically
extract structured candidate information. Handles the wide variety
of resume layouts that rule-based extraction cannot reliably parse.

TODO: Implement PDF text extraction with PyMuPDF in Phase 7 / Phase 8.
TODO: Implement Gemini-based extraction in Phase 8.
"""

from __future__ import annotations

import logging
from typing import Any

from app.clients.base import AiClient
from app.domain.models import CanonicalCandidate
from app.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class PdfResumeParser(BaseParser):
    """
    Parser for PDF-format resumes.

    Uses a two-stage extraction process:
    1. Extract raw text from the PDF using PyMuPDF.
    2. Send extracted text to Gemini for semantic parsing into
       structured candidate data.

    Depends on an AiClient abstraction for AI extraction, enabling
    unit testing with MockGeminiClient.

    TODO: Implement PDF text extraction.
    TODO: Implement Gemini extraction call.
    TODO: Handle extraction failures gracefully (return partial data).
    """

    def __init__(self, ai_client: AiClient) -> None:
        """
        Initialize the PDF resume parser.

        Args:
            ai_client: AiClient instance for AI extraction.
        """
        self._ai_client = ai_client
        logger.debug("PdfResumeParser initialized")

    def parse(self, raw_data: str | bytes, **kwargs: Any) -> CanonicalCandidate:
        """
        Parse a PDF resume into a CanonicalCandidate.

        Args:
            raw_data: PDF file content as bytes.
            **kwargs: Optional extraction parameters.

        Returns:
            CanonicalCandidate with parsed fields.

        Raises:
            ParsingError: If the PDF cannot be read or extraction fails.
        """
        # TODO: Implement PDF parsing
        logger.warning("PdfResumeParser.parse is not yet implemented")
        raise NotImplementedError("PDF resume parsing is not yet implemented")
