"""
Provenance model and generic wrapper for field-level provenance.

Tracks the origin and extraction details of candidate data.
The ``Provenanced[T]`` generic type wraps any value with its
provenance and confidence, enabling granular field-level
tracking across multiple sources.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SourceType(StrEnum):
    """
    Supported data source types.

    StrEnum enables clean JSON serialization — values are plain
    strings. Adding a new source type requires adding a member
    to this enum and registering the corresponding parser.
    """

    CSV = "csv"
    ATS_JSON = "ats_json"
    PDF_RESUME = "pdf_resume"
    TXT_NOTES = "txt_notes"
    LINKEDIN = "linkedin"
    GITHUB = "github"
    WORKDAY = "workday"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    SUCCESSFACTORS = "successfactors"
    NAUKRI = "naukri"
    INDEED = "indeed"


# Backward-compatible module-level constants
SOURCE_TYPE_CSV = SourceType.CSV
SOURCE_TYPE_ATS_JSON = SourceType.ATS_JSON
SOURCE_TYPE_PDF_RESUME = SourceType.PDF_RESUME
SOURCE_TYPE_TXT_NOTES = SourceType.TXT_NOTES
SOURCE_TYPE_LINKEDIN = SourceType.LINKEDIN
SOURCE_TYPE_GITHUB = SourceType.GITHUB
SOURCE_TYPE_WORKDAY = SourceType.WORKDAY
SOURCE_TYPE_GREENHOUSE = SourceType.GREENHOUSE
SOURCE_TYPE_LEVER = SourceType.LEVER
SOURCE_TYPE_SUCCESSFACTORS = SourceType.SUCCESSFACTORS
SOURCE_TYPE_NAUKRI = SourceType.NAUKRI
SOURCE_TYPE_INDEED = SourceType.INDEED


class Provenance(BaseModel):
    """
    Origin and processing metadata for candidate data.

    Captures where a piece of data came from, how it was
    extracted, and when. Attached at field level to support
    granular provenance tracking across multiple sources.

    Attributes:
        source_type: The original data source identifier.
        source_id: Identifier within the source (file name,
                   row ID, or record key).
        parser: Name of the parser that produced this data.
        extracted_at: When the data was extracted or parsed.
        confidence: Extraction confidence (0.0 – 1.0).
    """

    source_type: SourceType = SourceType.CSV
    source_id: str = ""
    parser: str = ""
    extracted_at: datetime = Field(default_factory=datetime.now)
    confidence: float = 0.0


class Provenanced(BaseModel, Generic[T]):
    """
    Generic wrapper pairing a value with its provenance.

    Enables field-level provenance tracking. Any domain value
    can be wrapped with ``Provenanced`` to know where it came
    from and how reliable it is.

    Example:
        email = Provenanced[str](
            value="john@example.com",
            provenance=Provenance(source_type=SourceType.CSV),
        )

    Attributes:
        value: The underlying domain value.
        provenance: Origin and extraction metadata.
    """

    value: T
    provenance: Provenance = Field(default_factory=Provenance)
