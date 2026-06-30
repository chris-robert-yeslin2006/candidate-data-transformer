"""
CanonicalCandidate — the universal data model.

Every parser produces a CanonicalCandidate and every downstream service
consumes one. This is the heart of the system.

All fields are optional to support partial data from any source.

TODO: Refine field list and validation in Phase 2 review.
"""

from pydantic import BaseModel

from app.domain.models.education import Education
from app.domain.models.experience import Experience


class CanonicalCandidate(BaseModel):
    """
    Universal candidate representation.

    Attributes:
        name: Candidate's full name.
        phone: Contact phone number (raw; normalizer handles formatting).
        email: Email address (lowercased by normalizer).
        address: Physical address text.
        skills: List of skill strings.
        experience: Ordered list of work experiences (most recent first).
        education: Ordered list of education entries (most recent first).
    """

    name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    skills: list[str] = []
    experience: list[Experience] = []
    education: list[Education] = []
