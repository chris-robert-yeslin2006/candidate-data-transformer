"""
Provenance — tracks the origin and processing history of candidate data.

Every CanonicalCandidate carries provenance metadata so downstream
consumers can audit where each value came from and how it was processed.

TODO: Add field-level provenance tracking in Phase 11.
"""

from datetime import datetime

from pydantic import BaseModel


class Provenance(BaseModel):
    """
    Origin and processing metadata for a candidate record.

    Attributes:
        source_type: The original data source (csv, pdf, txt, ats_json).
        parser: Name of the parser that produced this record.
        timestamp: When the parsing occurred.
        warnings: List of non-fatal warning messages from parsing.
    """

    source_type: str = ""
    parser: str = ""
    timestamp: datetime = datetime.fromtimestamp(0)
    warnings: list[str] = []
