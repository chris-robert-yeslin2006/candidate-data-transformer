"""
ATS JSON source parser.

Handles structured candidate data in JSON format, typically exported
from Applicant Tracking Systems. Maps JSON keys to canonical field
names using a configurable mapping.

TODO: Implement actual JSON parsing logic in Phase 5.
"""

from __future__ import annotations

import logging
from typing import Any

from app.domain.models import CanonicalCandidate
from app.domain.models.provenance import SourceType
from app.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class AtsJsonParser(BaseParser):
    """
    Parser for JSON-encoded candidate data from ATS exports.

    Reads JSON content, maps keys to canonical model fields, and
    returns a structured candidate representation. Supports optional
    key remapping for different ATS export formats.

    TODO: Implement JSON parsing with standard library json module.
    TODO: Add configurable key mapping support.
    TODO: Mark as optional — skipped if no ATS JSON sources exist.
    """

    source_type: SourceType = SourceType.ATS_JSON
    display_name: str = "ATS JSON Parser"
    supported_extensions: list[str] = [".json"]
    supported_mime_types: list[str] = ["application/json"]
    requires_ai: bool = False
    parser_version: str = "0.1.0"

    def parse(self, raw_data: str | bytes, **kwargs: Any) -> CanonicalCandidate:
        """
        Parse JSON content into a CanonicalCandidate.

        Args:
            raw_data: JSON content as a string.
            **kwargs: Optional key mapping overrides.

        Returns:
            CanonicalCandidate with parsed fields.

        Raises:
            ParsingError: If the JSON data is malformed.
        """
        # TODO: Implement JSON parsing
        logger.warning("AtsJsonParser.parse is not yet implemented")
        raise NotImplementedError("ATS JSON parsing is not yet implemented")
