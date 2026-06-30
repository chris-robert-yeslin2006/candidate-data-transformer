"""
Provenance model and generic wrapper for field-level provenance.

Tracks the origin and extraction details of candidate data.
The ``Provenanced[T]`` generic type wraps any value with its
provenance and confidence, enabling granular field-level
tracking across multiple sources.
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SourceType(str):
    """
    Supported data source types.

    String-based enum for extensibility. New sources can be
    added by registering a new source type string — no enum
    modification required.
    """


# Standard source type constants
SOURCE_TYPE_CSV = "csv"
SOURCE_TYPE_ATS_JSON = "ats_json"
SOURCE_TYPE_PDF_RESUME = "pdf_resume"
SOURCE_TYPE_TXT_NOTES = "txt_notes"
SOURCE_TYPE_LINKEDIN = "linkedin"
SOURCE_TYPE_GITHUB = "github"
SOURCE_TYPE_WORKDAY = "workday"
SOURCE_TYPE_GREENHOUSE = "greenhouse"
SOURCE_TYPE_LEVER = "lever"
SOURCE_TYPE_SUCCESSFACTORS = "successfactors"
SOURCE_TYPE_NAUKRI = "naukri"
SOURCE_TYPE_INDEED = "indeed"


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

    source_type: str = ""
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
            provenance=Provenance(source_type="csv"),
        )

    Attributes:
        value: The underlying domain value.
        provenance: Origin and extraction metadata.
    """

    value: T
    provenance: Provenance = Field(default_factory=Provenance)
