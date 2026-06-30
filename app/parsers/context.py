"""
ParserContext model.

Carries all runtime context a parser needs during a single
parse invocation: input metadata, shared services, logging,
and configuration.

The interface is designed for future adoption. Parsers currently
receive ``(raw_data, **kwargs)``. In a later phase, the signature
will evolve to ``parse(context: ParserContext) -> ParseResult``.

This model is available now so parsers can start accepting it
optionally, but the migration is deferred to avoid unnecessary
churn during early phases.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.clients.base import AiClient
from app.domain.models.provenance import SourceType


class ParserContext(BaseModel):
    """
    Runtime context for a single parse invocation.

    Bundles everything a parser might need: the raw input bytes,
    metadata about the source, shared services like AiClient,
    and caller-provided configuration overrides.

    Using a context object instead of scattered kwargs keeps
    the parser interface stable as new context fields are added.

    Attributes:
        raw_data: Raw input content (string for text formats,
                  bytes for binary formats).
        source_type: The type of source being parsed.
        filename: Original filename, if available.
        content_type: MIME type or format hint.
        source_id: Identifier for the source (file path, row key).
        ai_client: Optional AI client for AI-powered parsers.
        config: Free-form configuration overrides for the parser.
        reference_datetime: The logical "now" for date parsing.
    """

    raw_data: str | bytes
    source_type: SourceType
    filename: str = ""
    content_type: str = ""
    source_id: str = ""
    ai_client: AiClient | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    reference_datetime: datetime = Field(default_factory=datetime.now)
