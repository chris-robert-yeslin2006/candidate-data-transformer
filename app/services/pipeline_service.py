"""
Pipeline orchestration service.

Orchestrates the full data transformation pipeline from input files
to validated output. Owns the workflow sequence and handles partial
failures from individual sources.

Uses dependency injection for all sub-services: parser factory,
normalization service, merge engine, confidence service, projection
service, and validation service. The pipeline owns the sequence but
not the implementation of individual stages.
"""

from __future__ import annotations

import logging
from typing import Any

from app.parsers.registry import ParserFactory

logger = logging.getLogger(__name__)


class PipelineService:
    """
    Orchestrates the candidate data transformation pipeline.

    Sequences every stage: parse -> baseline confidence -> normalise ->
    merge -> refine confidence -> project -> validate. Handles partial
    source failures by collecting warnings and continuing with
    available data.

    This service is the single entry point for all transformation
    requests. The FastAPI endpoint delegates to this service and
    returns its result.

    Attributes:
        parser_factory: Factory for creating parser instances.
    """

    def __init__(self, parser_factory: ParserFactory | None = None) -> None:
        """
        Initialize the pipeline service.

        Args:
            parser_factory: Optional ParserFactory for creating source
                           parsers. If None, no parsing is available.
        """
        self._parser_factory = parser_factory
        logger.info(
            "PipelineService initialized (parser_factory=%s)",
            "provided" if parser_factory else "none",
        )

    def process(
        self,
        files: list[dict[str, Any]],
        projection_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Execute the full transformation pipeline.

        Args:
            files: List of file descriptors, each containing raw data
                   and source type metadata.
            projection_config: Optional output schema configuration.

        Returns:
            Pipeline result containing transformed data, warnings,
            and provenance trail.

        Raises:
            NotImplementedError: Until the pipeline is fully wired.

        TODO: Implement pipeline stages.
        """
        if self._parser_factory:
            logger.debug(
                "Available parsers: %s", self._parser_factory.supported_types
            )

        logger.warning("PipelineService.process is not yet implemented")
        raise NotImplementedError("Pipeline processing is not yet implemented")
