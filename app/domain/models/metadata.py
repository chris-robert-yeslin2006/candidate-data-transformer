"""
Processing metadata for candidate records.

Tracks lifecycle timestamps, contributing sources, pipeline
versioning, and non-fatal warnings generated during pipeline
execution.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.models.warning import Warning as ProcessingWarning


class ProcessingMetadata(BaseModel):
    """
    Lifecycle and processing metadata for a candidate record.

    Captures when the record was created and last updated,
    which data sources contributed to it, which pipeline and
    parser versions processed it, who initiated the request,
    and any warnings raised during processing.

    Attributes:
        created_at: When the canonical record was first created.
        updated_at: When the record was last modified.
        pipeline_version: Version of the pipeline that processed
                          this record.
        parser_version: Version of the parser configuration used.
        created_by: Identifier of the user or system that initiated
                    the request.
        processing_duration: Total pipeline processing time in seconds.
        warnings: List of non-fatal processing warnings.
        source_types: Data source types that contributed to this record.
    """

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    pipeline_version: str = ""
    parser_version: str = ""
    created_by: str = ""
    processing_duration: float = 0.0
    warnings: list[ProcessingWarning] = []
    source_types: list[str] = []
