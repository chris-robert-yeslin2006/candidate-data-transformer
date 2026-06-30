"""
ParserMetadata model.

Describes a parser's capabilities, configuration, and version.
Exposed by every parser via the ``metadata`` class attribute
or classmethod. The registry uses metadata for introspection
and routing decisions.
"""

from pydantic import BaseModel, Field

from app.domain.models.provenance import SourceType


class ParserMetadata(BaseModel):
    """
    Describes what a parser handles and how it is configured.

    Every parser exposes its metadata so that the registry,
    factory, and pipeline can introspect parser capabilities
    without instantiating the parser.

    Attributes:
        source_type: The source type this parser handles.
        display_name: Human-readable name for logging and UIs.
        supported_extensions: File extensions this parser accepts
                              (e.g. [".csv", ".tsv"]).
        supported_mime_types: MIME types this parser accepts
                              (e.g. ["text/csv"]).
        requires_ai: Whether this parser depends on an AiClient.
        parser_version: Version string for this parser.
    """

    source_type: SourceType
    display_name: str = ""
    supported_extensions: list[str] = Field(default_factory=list)
    supported_mime_types: list[str] = Field(default_factory=list)
    requires_ai: bool = False
    parser_version: str = "0.1.0"
