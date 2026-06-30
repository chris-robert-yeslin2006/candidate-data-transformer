"""
Confidence score model.

Tracks data quality at the field and record level. Attached
to candidate data to communicate reliability to downstream
consumers. Baseline scores are source-based; refined scores
incorporate cross-source agreement and merge quality.
"""

from pydantic import BaseModel, Field


class Confidence(BaseModel):
    """
    Data quality confidence score.

    Provides a quantitative measure of data reliability at
    both the record level and per-field granularity. The
    ``factors`` dictionary gives human-readable reasons
    for the score.

    Attributes:
        overall: Record-level confidence (0.0 – 1.0).
        fields: Per-field confidence scores keyed by field path.
        factors: Human-readable factors contributing to the score
                 (e.g. {"source": "csv", "agreement": "high"}).
    """

    overall: float = Field(default=0.0, ge=0.0, le=1.0)
    fields: dict[str, float] = {}
    factors: dict[str, str] = {}
