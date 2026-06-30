"""
Abstract base parser interface.

All source-specific parsers inherit from BaseParser and implement
the parse method. This establishes a consistent contract: every
parser accepts raw data and returns a canonical model with metadata.

Subclasses must define a ``source_type`` class attribute that
identifies the data source this parser handles. This attribute
is used by ParserRegistry for automatic parser discovery and
registration.

Future evolution:
    The parse signature will eventually become:
        parse(context: ParserContext) -> ParseResult

    ParserContext bundles raw_data, source metadata, AI client,
    and configuration. ParseResult carries the candidate plus
    warnings, parser metadata, and processing statistics.
    These types are available now for opt-in adoption but the
    interface migration is deferred to a later phase.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.domain.models import CanonicalCandidate
from app.domain.models.provenance import SourceType
from app.parsers.metadata import ParserMetadata

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """
    Abstract base for all source-specific parsers.

    Every parser must implement ``parse()``, which converts raw input
    data into a canonical candidate model. Parsers encode format-
    specific extraction logic but never leak format-specific types
    into downstream services.

    Subclasses must define:
        source_type: A SourceType enum value identifying the format.

    Class Attributes:
        source_type: SourceType enum used by ParserRegistry.
        display_name: Human-readable name for logging and metadata.
        supported_extensions: File extensions this parser handles.
        supported_mime_types: MIME types this parser handles.
        requires_ai: Whether this parser needs an AiClient.
        parser_version: Version string for this parser.
    """

    source_type: SourceType = SourceType.CSV
    display_name: str = ""
    supported_extensions: list[str] = []
    supported_mime_types: list[str] = []
    requires_ai: bool = False
    parser_version: str = "0.1.0"

    @classmethod
    def metadata(cls) -> ParserMetadata:
        """
        Return a ParserMetadata describing this parser's capabilities.

        Uses class attributes by default. Subclasses can override
        this method to compute metadata dynamically.

        Returns:
            ParserMetadata instance populated from class attributes.
        """
        return ParserMetadata(
            source_type=cls.source_type,
            display_name=cls.display_name,
            supported_extensions=list(cls.supported_extensions),
            supported_mime_types=list(cls.supported_mime_types),
            requires_ai=cls.requires_ai,
            parser_version=cls.parser_version,
        )

    @abstractmethod
    def parse(self, raw_data: str | bytes, **kwargs: Any) -> CanonicalCandidate:
        """
        Parse raw input data into a canonical candidate structure.

        Args:
            raw_data: Raw input content (string for text formats,
                      bytes for binary formats like PDF).
            **kwargs: Optional format-specific parameters.

        Returns:
            CanonicalCandidate representing the parsed candidate.

        Raises:
            ParsingError: If the input cannot be parsed.
        """
        ...
