"""
Projection and validation layer.

Provides the ProjectionService for transforming canonical candidate
data into client-specific output schemas, and the ValidationService
for validating projected output against target schemas.
"""

from app.projections.nested_projection import NestedProjectionEngine
from app.projections.projection_service import ProjectionService
from app.projections.validation_service import ValidationService

__all__ = [
    "NestedProjectionEngine",
    "ProjectionService",
    "ValidationService",
]
