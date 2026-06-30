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
from app.api.schemas import ErrorDetailResponse, TransformJSONRequest, TransformResponse
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


@router.post(
    "/transform",
    response_model=TransformResponse,
    responses={
        400: {"model": ErrorDetailResponse, "description": "Bad Request - invalid input, configuration or validation schema"},
        500: {"model": ErrorDetailResponse, "description": "Internal Server Error - transformation pipeline processing failed"}
    },
    summary="Transform candidate data (Multipart)",
    description=(
        "Transform multi-source candidate data from uploaded files (CSV, JSON, PDF, TXT, MD) "
        "using an optional projection config and validation schema."
    ),
)
async def transform(
    request: Request,
    files: list[UploadFile] = File(
        default=[],
        description="List of candidate resumes/data files to upload and transform. Supported formats: .csv, .json, .pdf, .txt, .md",
    ),
    source_types: str = Form(
        default="",
        description=(
            "Comma-separated list of source type identifiers (one per file, e.g., 'csv,ats_json'). "
            "Supported: 'csv', 'ats_json', 'pdf_resume', 'txt_notes'. If not provided, auto-detected from file extensions."
        ),
        examples=["csv,ats_json"],
    ),
    projection_config: str = Form(
        default="",
        description=(
            "Optional JSON string defining a custom projection mapping, OR a predefined template filename "
            "(e.g., 'companyb' or 'config/companyb.json')."
        ),
        examples=["companyb"],
    ),
    validation_schema: str = Form(
        default="",
        description=(
            "Optional JSON string defining validation rules. "
            "Format: {'required': ['field_name'], 'types': {'field_name': 'type_str'}}."
        ),
        examples=['{"required": ["full_name", "email"], "types": {"full_name": "string"}}'],
    ),
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


@router.post(
    "/transform/json",
    response_model=TransformResponse,
    responses={
        400: {"model": ErrorDetailResponse, "description": "Bad Request - invalid input, configuration or validation schema"},
        500: {"model": ErrorDetailResponse, "description": "Internal Server Error - transformation pipeline processing failed"}
    },
    summary="Transform candidate data (JSON Body)",
    description=(
        "Transform multi-source candidate data provided inline in a JSON request body, "
        "using an optional projection config and validation schema."
    ),
)
async def transform_json(
    request: Request,
    payload: TransformJSONRequest,
) -> JSONResponse:
    """
    Transform candidate data from a JSON request body.

    Alternative to the multipart form upload. Accepts a JSON body
    with inline source data.
    """
    pipeline_service = request.app.state.pipeline_service

    sources = payload.sources
    if not sources:
        return JSONResponse(
            status_code=400,
            content={"error": "No sources provided"},
        )

    file_descriptors = [
        {
            "raw_data": src.raw_data,
            "source_type": src.source_type,
            "source_id": src.source_id or f"source_{i}",
        }
        for i, src in enumerate(sources)
    ]

    proj_config = None
    if payload.projection_config is not None:
        try:
            proj_config = _resolve_projection_config(payload.projection_config)
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
            validation_schema=payload.validation_schema,
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


@router.get("/gui/samples")
async def list_gui_samples() -> dict[str, Any]:
    """
    List names, contents, and autodetected source types of all files in samples/ directory.
    """
    import os
    samples_dir = "samples"
    samples_data = []

    if os.path.exists(samples_dir):
        for filename in os.listdir(samples_dir):
            if filename == ".gitkeep":
                continue
            path = os.path.join(samples_dir, filename)
            if os.path.isfile(path):
                try:
                    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
                    source_type = "csv"
                    if ext == "json":
                        source_type = "ats_json"
                    elif ext in ("txt", "md"):
                        source_type = "txt_notes"
                    elif ext == "pdf":
                        source_type = "pdf_resume"

                    # For PDFs, send empty content so UI knows it's a binary file
                    if ext == "pdf":
                        content = ""
                    else:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read()

                    samples_data.append({
                        "name": filename,
                        "content": content,
                        "source_type": source_type
                    })
                except Exception as e:
                    logger.error("Failed to read sample file %s: %s", filename, e)

    return {"samples": samples_data}


@router.get("/gui/templates")
async def list_gui_templates() -> dict[str, Any]:
    """
    List names and JSON contents of all projection templates in config/ directory.
    """
    import os
    config_dir = "config"
    templates = []

    if os.path.exists(config_dir):
        for filename in os.listdir(config_dir):
            if filename.endswith(".json"):
                path = os.path.join(config_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    templates.append({
                        "name": filename.rsplit(".", 1)[0],
                        "filename": filename,
                        "content": data
                    })
                except Exception as e:
                    logger.error("Failed to read template %s: %s", filename, e)

    return {"templates": templates}

