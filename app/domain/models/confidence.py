"""
ConfidenceScore — tracks data quality at field and record level.

Attached to every CanonicalCandidate to communicate reliability
to downstream consumers. Baseline scores come from source type;
refined scores incorporate cross-source agreement and merge quality.

TODO: Implement scoring logic in Phase 9 / Phase 12.
"""

from pydantic import BaseModel


class ConfidenceScore(BaseModel):
    """
    Data quality score for a candidate record.

    Attributes:
        overall: Record-level confidence (0.0 – 1.0).
        fields: Per-field confidence scores keyed by field name.
        factors: Human-readable map of contributing factors
                 (e.g. {"source": "csv", "agreement": "high"}).
    """

    overall: float = 0.0
    fields: dict[str, float] = {}
    factors: dict[str, str] = {}
