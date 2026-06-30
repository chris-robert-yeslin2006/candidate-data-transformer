"""API schemas for Candidate Data Transformer."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class JSONSourceInput(BaseModel):
    """
    Input schema for an inline data source.
    """
    source_type: str = Field(
        ...,
        description="Source type identifier. E.g. 'csv', 'ats_json', 'pdf_resume', 'txt_notes'.",
        examples=["csv"]
    )
    raw_data: str = Field(
        ...,
        description="The raw string content of the data file (e.g. CSV text, JSON text, or plain text notes).",
        examples=["name,email\nJohn Doe,john@example.com"]
    )
    source_id: str | None = Field(
        None,
        description="Unique identifier or filename for the source file.",
        examples=["candidates.csv"]
    )


class TransformJSONRequest(BaseModel):
    """
    Request schema for the JSON transform endpoint.
    """
    sources: list[JSONSourceInput] = Field(
        ...,
        description="List of inline candidate data sources to transform."
    )
    projection_config: dict[str, Any] | str | None = Field(
        None,
        description=(
            "Optional custom projection config (dictionary) OR template name / path "
            "(e.g., 'companyb' or 'config/companyb.json')."
        ),
        examples=["companyb"]
    )
    validation_schema: dict[str, Any] | None = Field(
        None,
        description="Optional validation schema specifying required fields and types.",
        examples=[{"required": ["full_name"], "types": {"full_name": "string"}}]
    )


class ConfidenceResponse(BaseModel):
    """
    Granular confidence score metadata.
    """
    overall: float = Field(
        ...,
        description="Overall confidence score for the candidate (0.0 to 1.0).",
        examples=[0.85]
    )
    fields: dict[str, float] = Field(
        ...,
        description="Confidence scores for individual fields.",
        examples=[{"full_name": 0.9, "email": 0.95}]
    )
    factors: dict[str, Any] = Field(
        ...,
        description="Scoring breakdown showing the justification/factors behind the field scores.",
        examples=[{"full_name": ["complete_match"], "email": ["valid_domain"]}]
    )


class WarningResponse(BaseModel):
    """
    Warning details generated during the transformation pipeline.
    """
    message: str = Field(
        ...,
        description="Human-readable description of the warning.",
        examples=["Missing field 'phone' during parsing."]
    )
    source: str = Field(
        ...,
        description="The component or service that triggered this warning.",
        examples=["csv_parser"]
    )
    code: str = Field(
        ...,
        description="Standardized error/warning code.",
        examples=["MISSING_FIELD"]
    )
    field: str | None = Field(
        None,
        description="The candidate field associated with this warning, if applicable.",
        examples=["phone"]
    )


class TransformResponse(BaseModel):
    """
    Response schema representing the outcome of a successful transformation pipeline.
    """
    data: dict[str, Any] = Field(
        ...,
        description="The transformed and projected candidate data based on default or customized configurations.",
        examples=[
            {
                "full_name": "John Doe",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": None,
                "skills": ["Python", "SQL"],
                "summary": "Software Developer",
                "experience": [],
                "education": []
            }
        ]
    )
    confidence: ConfidenceResponse = Field(
        ...,
        description="Scoring details detailing the reliability of parsed/merged candidate information."
    )
    warnings: list[WarningResponse] = Field(
        ...,
        description="Collection of warnings, validation issues, or parse failures gathered during pipeline stages."
    )
    provenance: list[str] = Field(
        ...,
        description="List of unique source types contributing to the merged candidate record.",
        examples=[["csv", "ats_json"]]
    )
    processing_duration: float = Field(
        ...,
        description="Time taken in seconds to run all transformation pipeline stages.",
        examples=[0.0234]
    )
    is_valid: bool = Field(
        ...,
        description="Whether the output successfully conformed to the target schema constraints.",
        examples=[True]
    )


class ErrorDetailResponse(BaseModel):
    """
    Error details response schema for HTTP 400 and 500 status codes.
    """
    error: str = Field(
        ...,
        description="Brief name or error type.",
        examples=["Invalid projection_config"]
    )
    detail: str = Field(
        ...,
        description="Details explaining why the request failed.",
        examples=["Not a valid JSON or template name 'companyx'."]
    )
