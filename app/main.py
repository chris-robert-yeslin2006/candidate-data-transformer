"""
Application entry point.

Creates and configures the FastAPI application, sets up logging,
loads configuration, creates the parser factory, and wires
dependencies via dependency injection.

This module should remain thin — it wires the application together
and starts the server. All business logic lives in domain services.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.clients.gemini import GeminiClient
from app.config.settings import get_settings
from app.core.logging import configure_logging
from app.normalizers.normalization_service import NormalizationService
from app.parsers import default_registry
from app.parsers.registry import ParserFactory
from app.projections.projection_service import ProjectionService
from app.projections.validation_service import ValidationService
from app.services.confidence_service import ConfidenceService
from app.services.merge_engine import MergeEngine
from app.services.pipeline_service import PipelineService

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Loads settings, configures logging, creates shared services,
    wires dependencies, and registers route handlers.
    Called by the ASGI server (uvicorn) to instantiate the application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)

    # --- Service wiring (dependency injection) ---

    # Create the AI client (no-op until API is implemented)
    ai_client = None
    if settings.GEMINI_API_KEY:
        ai_client = GeminiClient(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
        )

    # Note: default_registry is already frozen after parser registration.
    # The factory wraps a frozen registry — no runtime additions allowed.
    parser_factory = ParserFactory(
        registry=default_registry,
        default_ai_client=ai_client,
    )

    # Create all pipeline services
    normalization_service = NormalizationService()
    confidence_service = ConfidenceService()
    merge_engine = MergeEngine()
    projection_service = ProjectionService()
    validation_service = ValidationService()

    # Create the pipeline service with all dependencies
    pipeline_service = PipelineService(
        parser_factory=parser_factory,
        normalization_service=normalization_service,
        confidence_service=confidence_service,
        merge_engine=merge_engine,
        projection_service=projection_service,
        validation_service=validation_service,
    )

    # --- FastAPI application ---

    app_description = """
### Multi-Source Candidate Data Transformation Service

This service parses, normalizes, merges, projects, and validates candidate profiles from multiple data sources.

---

### Key Capabilities

1. **Multi-Format Parsing**:
   - **CSV / TSV**: Raw or structured tables (autodetected or tagged as `csv`).
   - **ATS JSON**: Structured profiles (autodetected or tagged as `ats_json`).
   - **PDF Resumes**: Extracts name, email, skills, and work history (autodetected or tagged as `pdf_resume`).
   - **Text/Markdown Notes**: Recruiter or interviewer notes (autodetected or tagged as `txt_notes`).

2. **Granular Normalization & Merging**:
   - Field-by-field normalization (e.g., telephone formatting, name parsing).
   - De-duplicates and merges entries using confidence-based resolution, preserving source tracking (provenance).

3. **Projection Configuration**:
   - Tailor the JSON output to specific schemas without code changes.
   - Use predefined templates by sending name keys like `companyb` (looks up `config/companyb.json`), or pass a custom JSON mapping definition.

4. **Schema Validation**:
   - Validate target output against expected field requirements and data types.

---

### How to use these Endpoints:

- **Multipart File Upload (`/api/v1/transform`)**:
  Ideal for uploading multiple actual resume/profile documents. You can explicitly tag files with `source_types` or let the server auto-detect based on extensions.
- **JSON Request Payload (`/api/v1/transform/json`)**:
  Ideal for programmatic integrations where raw text content is provided inline within a single request body.
"""

    app = FastAPI(
        title="Candidate Data Transformer",
        description=app_description.strip(),
        version="0.1.0",
        swagger_ui_parameters={
            "tryItOutEnabled": True,
            "defaultModelsExpandDepth": 2,
            "filter": True,
            "displayRequestDuration": True,
        }
    )

    app.include_router(router, prefix="/api/v1")

    # Serve static assets
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def serve_gui():
        """Serve the interactive candidate data transformer Web GUI."""
        return FileResponse(os.path.join("app", "static", "index.html"))

    # Store shared services on the app state for route handlers
    app.state.parser_factory = parser_factory
    app.state.pipeline_service = pipeline_service

    logger.info(
        "Application created (host=%s, port=%s, log_level=%s, parsers=%s)",
        settings.APP_HOST,
        settings.APP_PORT,
        settings.LOG_LEVEL,
        [str(t) for t in parser_factory.supported_types],
    )

    return app


app = create_app()
