"""
Domain layer — enterprise business rules.

Contains the canonical data model (CanonicalCandidate), value objects
(Experience, Education, ConfidenceScore, Provenance), and domain
services. No framework, I/O, or infrastructure imports here.
"""

from app.domain.models import (
    CanonicalCandidate,
    ConfidenceScore,
    Education,
    Experience,
    Provenance,
)

__all__ = [
    "CanonicalCandidate",
    "ConfidenceScore",
    "Education",
    "Experience",
    "Provenance",
]
