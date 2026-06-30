"""
API route definitions.

This module is intentionally minimal. Routes delegate all business
logic to PipelineService. No business logic lives in route handlers.
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from app import __version__
from app.domain.models.provenance import SourceType

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns service status, version, and name.
    TODO: Add dependency health checks (Gemini API reachability, etc.).
    """
    logger.debug("Health check requested")
    return {
        "status": "healthy",
        "version": __version__,
        "service": "candidate-transformer",
    }


@router.post("/transform")
async def transform(
    request: Request,
    files: list[UploadFile] = File(default=[]),
    source_types: str = Form(default=""),
    projection_config: str = Form(default=""),
    validation_schema: str = Form(default=""),
) -> JSONResponse:
    """
    Transform candidate data from multiple sources.

    Accepts multipart file uploads with source type metadata.
    Delegates to PipelineService for the full transformation
    pipeline: parse → normalize → merge → project → validate.

    Args:
        request: FastAPI request object (for accessing app state).
        files: List of uploaded files.
        source_types: Comma-separated source type identifiers,
                     one per file. If not provided, auto-detects
                     from file extension.
        projection_config: Optional JSON string with projection config.
        validation_schema: Optional JSON string with validation schema.

    Returns:
        JSON response with transformed data, confidence scores,
        warnings, and provenance.
    """
    pipeline_service = request.app.state.pipeline_service

    # Parse source types
    type_list = [s.strip() for s in source_types.split(",") if s.strip()] if source_types else []

    # Build file descriptors
    file_descriptors: list[dict[str, Any]] = []
    for i, upload_file in enumerate(files):
        raw_data = await upload_file.read()

        # Determine source type
        if i < len(type_list):
            source_type = type_list[i]
        else:
            source_type = _detect_source_type(upload_file.filename or "")

        file_descriptors.append({
            "raw_data": raw_data,
            "source_type": source_type,
            "source_id": upload_file.filename or f"file_{i}",
        })

    if not file_descriptors:
        return JSONResponse(
            status_code=400,
            content={
                "error": "No files provided",
                "detail": "At least one file must be uploaded for transformation.",
            },
        )

    # Parse optional configs
    proj_config = None
    if projection_config:
        try:
            proj_config = _resolve_projection_config(projection_config)
        except ValueError as exc:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid projection_config",
                    "detail": str(exc),
                },
            )

    val_schema = None
    if validation_schema:
        try:
            val_schema = json.loads(validation_schema)
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid validation_schema",
                    "detail": "validation_schema must be valid JSON.",
                },
            )

    # Execute pipeline
    try:
        result = pipeline_service.process(
            files=file_descriptors,
            projection_config=proj_config,
            validation_schema=val_schema,
        )
        return JSONResponse(
            status_code=200,
            content=result.to_dict(),
        )
    except Exception as exc:
        logger.exception("Pipeline processing failed")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Pipeline processing failed",
                "detail": str(exc),
            },
        )


@router.post("/transform/json")
async def transform_json(
    request: Request,
) -> JSONResponse:
    """
    Transform candidate data from a JSON request body.

    Alternative to the multipart form upload. Accepts a JSON body
    with inline source data.

    Expected body:
    {
        "sources": [
            {
                "source_type": "csv",
                "raw_data": "name,email\\nJohn,john@example.com",
                "source_id": "candidates.csv"
            }
        ],
        "projection_config": { ... },
        "validation_schema": { ... }
    }
    """
    pipeline_service = request.app.state.pipeline_service

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON body"},
        )

    sources = body.get("sources", [])
    if not sources:
        return JSONResponse(
            status_code=400,
            content={"error": "No sources provided"},
        )

    file_descriptors = [
        {
            "raw_data": src.get("raw_data", ""),
            "source_type": src.get("source_type", "csv"),
            "source_id": src.get("source_id", f"source_{i}"),
        }
        for i, src in enumerate(sources)
    ]

    proj_config = None
    if "projection_config" in body:
        try:
            proj_config = _resolve_projection_config(body.get("projection_config"))
        except ValueError as exc:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid projection_config",
                    "detail": str(exc),
                },
            )

    try:
        result = pipeline_service.process(
            files=file_descriptors,
            projection_config=proj_config,
            validation_schema=body.get("validation_schema"),
        )
        return JSONResponse(
            status_code=200,
            content=result.to_dict(),
        )
    except Exception as exc:
        logger.exception("Pipeline processing failed")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Pipeline processing failed",
                "detail": str(exc),
            },
        )


def _detect_source_type(filename: str) -> str:
    """
    Auto-detect source type from file extension.

    Args:
        filename: The uploaded file's name.

    Returns:
        Source type string.
    """
    ext = filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""
    extension_map = {
        "csv": SourceType.CSV,
        "tsv": SourceType.CSV,  # CSVReader handles TSV too
        "json": SourceType.ATS_JSON,
        "pdf": SourceType.PDF_RESUME,
        "txt": SourceType.TXT_NOTES,
        "md": SourceType.TXT_NOTES,
    }
    return str(extension_map.get(ext, SourceType.CSV))


def _resolve_projection_config(projection_config: Any) -> dict[str, Any] | None:
    """
    Resolve projection configuration as inline JSON or template name.
    """
    if not projection_config:
        return None

    if isinstance(projection_config, dict):
        return projection_config

    if isinstance(projection_config, str):
        # 1. Try to parse as inline JSON
        try:
            return json.loads(projection_config)
        except json.JSONDecodeError:
            # 2. Try to load from root config/ folder
            import os
            clean_name = os.path.basename(projection_config).strip().lower()
            if not clean_name.endswith(".json"):
                clean_name = f"{clean_name}.json"
            
            template_path = os.path.join("config", clean_name)
            if os.path.exists(template_path):
                try:
                    with open(template_path, "r") as f:
                        return json.load(f)
                except Exception as exc:
                    logger.error("Failed to read template file %s: %s", template_path, exc)
            
            raise ValueError(f"Invalid projection_config: Not a valid JSON or template name '{projection_config}'.")

    return None
