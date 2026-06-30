"""
Application services layer.

Contains the pipeline orchestrator and supporting services
for normalization, confidence scoring, merging, projection,
and validation.
"""

from app.services.confidence_service import ConfidenceService
from app.services.merge_engine import MergeEngine
from app.services.pipeline_service import PipelineResult, PipelineService

__all__ = [
    "ConfidenceService",
    "MergeEngine",
    "PipelineResult",
    "PipelineService",
]
