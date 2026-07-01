"""
ParseResult model.

Separates the parsed candidate from its processing metadata and
warnings. Every parser's ``parse_with_context()`` returns a
ParseResult, keeping candidate data clean of lifecycle concerns.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.models import CanonicalCandidate, ProcessingMetadata, ProcessingWarning


class ParseResult(BaseModel):
    """
    Outcome of a single parse invocation.

    Separates the parsed candidate from its processing metadata,
    warnings, and provenance. This allows downstream services to
    work with the candidate data without worrying about how it
    was produced, while keeping audit information accessible.

    Attributes:
        candidate: The parsed canonical candidate.
        metadata: Processing lifecycle metadata.
        warnings: Warnings generated during parsing.
        parser_version: Version of the parser used.
        source_types: Source types that contributed.
        processing_duration: Time taken to parse in seconds.
    """

    candidate: CanonicalCandidate
    metadata: ProcessingMetadata = Field(default_factory=ProcessingMetadata)
    warnings: list[ProcessingWarning] = Field(default_factory=list)
    parser_version: str = ""
    source_types: list[str] = Field(default_factory=list)
    processing_duration: float = 0.0

    @classmethod
    def from_candidate(
        cls,
        candidate: CanonicalCandidate,
        parser_version: str = "",
        source_types: list[str] | None = None,
        warnings: list[ProcessingWarning] | None = None,
        processing_duration: float = 0.0,
    ) -> ParseResult:
        """
        Build a ParseResult from an existing candidate and metadata.

        Args:
            candidate: The parsed candidate.
            parser_version: Version of the parser.
            source_types: Source types that contributed.
            warnings: Warnings generated during parsing.
            processing_duration: Parse duration in seconds.

        Returns:
            A fully populated ParseResult.
        """
        now = datetime.now()
        return cls(
            candidate=candidate,
            metadata=ProcessingMetadata(
                created_at=now,
                updated_at=now,
                parser_version=parser_version,
                source_types=source_types or [],
                processing_duration=processing_duration,
                warnings=warnings or [],
            ),
            warnings=warnings or [],
            parser_version=parser_version,
            source_types=source_types or [],
            processing_duration=processing_duration,
        )
