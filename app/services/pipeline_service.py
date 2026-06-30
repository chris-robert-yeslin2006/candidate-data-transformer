"""
Pipeline orchestration service.

Orchestrates the full data transformation pipeline from input files
to validated output. Owns the workflow sequence and handles partial
failures from individual sources.

Pipeline stages:
    1. Parse each source → CanonicalCandidate
    2. Assign baseline confidence scores
    3. Normalize all candidates
    4. Merge candidates into single record
    5. Compute refined confidence
    6. Apply projection config (optional)
    7. Validate output (optional)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

from app.domain.models import CanonicalCandidate
from app.domain.models.confidence import Confidence
from app.domain.models.metadata import ProcessingMetadata
from app.domain.models.provenance import SourceType
from app.domain.models.warning import Warning as ProcessingWarning
from app.normalizers.normalization_service import NormalizationService
from app.parsers.registry import ParserFactory
from app.projections.projection_service import ProjectionService
from app.projections.validation_service import ValidationService
from app.services.confidence_service import ConfidenceService
from app.services.merge_engine import MergeEngine

logger = logging.getLogger(__name__)


class PipelineResult:
    """
    Result of the pipeline processing.

    Attributes:
        data: Projected output dictionary (or raw candidate dict).
        candidate: The merged CanonicalCandidate.
        confidence: Refined confidence scores.
        warnings: All warnings from every pipeline stage.
        provenance: Source types that contributed to the result.
        processing_duration: Total pipeline processing time in seconds.
        is_valid: Whether the output passed schema validation.
    """

    def __init__(
        self,
        data: dict[str, Any],
        candidate: CanonicalCandidate,
        confidence: Confidence,
        warnings: list[ProcessingWarning],
        provenance: list[str],
        processing_duration: float = 0.0,
        is_valid: bool = True,
    ) -> None:
        self.data = data
        self.candidate = candidate
        self.confidence = confidence
        self.warnings = warnings
        self.provenance = provenance
        self.processing_duration = processing_duration
        self.is_valid = is_valid

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "data": self.data,
            "confidence": {
                "overall": self.confidence.overall,
                "fields": self.confidence.fields,
                "factors": self.confidence.factors,
            },
            "warnings": [
                {
                    "message": w.message,
                    "source": w.source,
                    "code": w.code,
                    "field": w.field,
                }
                for w in self.warnings
            ],
            "provenance": self.provenance,
            "processing_duration": round(self.processing_duration, 4),
            "is_valid": self.is_valid,
        }


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
    """

    def __init__(
        self,
        parser_factory: ParserFactory | None = None,
        normalization_service: NormalizationService | None = None,
        confidence_service: ConfidenceService | None = None,
        merge_engine: MergeEngine | None = None,
        projection_service: ProjectionService | None = None,
        validation_service: ValidationService | None = None,
    ) -> None:
        """
        Initialize the pipeline service.

        Args:
            parser_factory: Factory for creating source parsers.
            normalization_service: Service for normalizing candidate fields.
            confidence_service: Service for confidence scoring.
            merge_engine: Engine for merging multiple candidates.
            projection_service: Service for projecting to output schemas.
            validation_service: Service for validating projected output.
        """
        self._parser_factory = parser_factory
        self._normalization_service = normalization_service or NormalizationService()
        self._confidence_service = confidence_service or ConfidenceService()
        self._merge_engine = merge_engine or MergeEngine()
        self._projection_service = projection_service or ProjectionService()
        self._validation_service = validation_service or ValidationService()
        logger.info(
            "PipelineService initialized (parser_factory=%s)",
            "provided" if parser_factory else "none",
        )

    def process(
        self,
        files: list[dict[str, Any]],
        projection_config: dict[str, Any] | None = None,
        validation_schema: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """
        Execute the full transformation pipeline.

        Args:
            files: List of file descriptors, each containing:
                - raw_data: Raw file content (str or bytes)
                - source_type: SourceType enum value or string
                - source_id: Optional identifier for the source
            projection_config: Optional output schema configuration.
            validation_schema: Optional validation schema.

        Returns:
            PipelineResult with transformed data, confidence,
            warnings, and provenance.
        """
        start_time = time.time()
        all_warnings: list[ProcessingWarning] = []

        # Stage 1: Parse each source
        candidates: list[CanonicalCandidate] = []
        source_types: list[SourceType] = []

        for file_desc in files:
            raw_data = file_desc.get("raw_data", "")
            source_type = file_desc.get("source_type", SourceType.CSV)
            source_id = file_desc.get("source_id", "")

            # Convert string source type to enum
            if isinstance(source_type, str):
                try:
                    source_type = SourceType(source_type)
                except ValueError:
                    all_warnings.append(
                        ProcessingWarning(
                            message=f"Unknown source type: {source_type}",
                            source="pipeline",
                            code="UNKNOWN_SOURCE_TYPE",
                            field="",
                        )
                    )
                    continue

            candidate = self._parse_source(
                raw_data, source_type, source_id, all_warnings
            )
            if candidate is not None:
                candidates.append(candidate)
                source_types.append(source_type)

        if not candidates:
            return PipelineResult(
                data={},
                candidate=CanonicalCandidate(),
                confidence=Confidence(),
                warnings=all_warnings,
                provenance=[],
                processing_duration=time.time() - start_time,
                is_valid=False,
            )

        # Stage 2: Baseline confidence scoring
        confidences: list[Confidence] = []
        for cand, st in zip(candidates, source_types):
            conf = self._confidence_service.score_baseline(st, cand)
            confidences.append(conf)

        # Stage 3: Normalize all candidates
        for i, cand in enumerate(candidates):
            normalized, norm_warnings = self._normalization_service.normalize(cand)
            candidates[i] = normalized
            all_warnings.extend(norm_warnings)

        # Stage 4: Merge candidates
        merged, merge_warnings = self._merge_engine.merge(
            candidates, source_types, confidences
        )
        all_warnings.extend(merge_warnings)

        # Stage 5: Refined confidence scoring
        refined_confidence = self._confidence_service.score_refined(
            merged, candidates, source_types
        )

        # Stage 6: Projection
        projected, proj_warnings = self._projection_service.project(
            merged, projection_config
        )
        all_warnings.extend(proj_warnings)

        # Stage 7: Validation
        is_valid, val_warnings = self._validation_service.validate(
            projected, validation_schema
        )
        all_warnings.extend(val_warnings)

        processing_duration = time.time() - start_time

        # Attach metadata to merged candidate
        merged.metadata = ProcessingMetadata(
            created_at=datetime.now(),
            updated_at=datetime.now(),
            pipeline_version="1.0.0",
            processing_duration=processing_duration,
            source_types=[str(st) for st in source_types],
            warnings=all_warnings,
        )

        return PipelineResult(
            data=projected,
            candidate=merged,
            confidence=refined_confidence,
            warnings=all_warnings,
            provenance=[str(st) for st in source_types],
            processing_duration=processing_duration,
            is_valid=is_valid,
        )

    def _parse_source(
        self,
        raw_data: str | bytes,
        source_type: SourceType,
        source_id: str,
        warnings: list[ProcessingWarning],
    ) -> CanonicalCandidate | None:
        """
        Parse a single source, catching failures gracefully.

        Args:
            raw_data: Raw content.
            source_type: Source type identifier.
            source_id: Source identifier.
            warnings: Warning accumulator.

        Returns:
            Parsed CanonicalCandidate, or None on failure.
        """
        if not self._parser_factory:
            warnings.append(
                ProcessingWarning(
                    message="No parser factory configured",
                    source="pipeline",
                    code="NO_PARSER_FACTORY",
                    field="",
                )
            )
            return None

        try:
            parser = self._parser_factory.create(source_type)
            candidate = parser.parse(raw_data, source_id=source_id)
            logger.info(
                "Successfully parsed %s source (id=%s)",
                source_type, source_id,
            )
            return candidate
        except KeyError:
            warnings.append(
                ProcessingWarning(
                    message=f"No parser available for source type: {source_type}",
                    source="pipeline",
                    code="NO_PARSER",
                    field="",
                )
            )
            return None
        except NotImplementedError as exc:
            warnings.append(
                ProcessingWarning(
                    message=f"Parser for {source_type} is not yet implemented: {exc}",
                    source="pipeline",
                    code="PARSER_NOT_IMPLEMENTED",
                    field="",
                )
            )
            return None
        except Exception as exc:
            warnings.append(
                ProcessingWarning(
                    message=f"Failed to parse {source_type} source: {exc}",
                    source="pipeline",
                    code="PARSE_ERROR",
                    field="",
                )
            )
            logger.exception("Parser failed for %s", source_type)
            return None
