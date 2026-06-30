"""
CanonicalCandidate — the universal data model and aggregate root.

Every parser produces a CanonicalCandidate and every downstream
service consumes one. This model is the single source of truth
for candidate information in the system.
"""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.models.certification import Certification
from app.domain.models.contact import ContactInformation
from app.domain.models.education import Education
from app.domain.models.experience import Experience
from app.domain.models.metadata import ProcessingMetadata
from app.domain.models.organization import Organization
from app.domain.models.person_name import PersonName
from app.domain.models.project import Project
from app.domain.models.skill import Skill


class CanonicalCandidate(BaseModel):
    """
    Universal candidate representation — the aggregate root.

    Aggregates all candidate information into a single model that
    serves as the system's canonical representation. Every parser
    converts source-specific formats into this model, and every
    downstream service (normalization, merge, projection) consumes it.

    All collection fields default to empty lists so that partial
    candidates from any source are valid. The ``id`` field provides
    a stable identifier for merge and deduplication operations.

    Attributes:
        id: Stable unique identifier for this candidate.
        name: Structured full name of the candidate.
        contact: Aggregated contact information (email, phone,
                 social links, location).
        skills: List of skills with categorization and aliases.
        experience: Ordered list of work experiences (most recent first).
        education: Ordered list of education entries (most recent first).
        certifications: List of professional certifications.
        projects: List of projects (personal, academic, or professional).
        organizations: List of organizational involvements.
        summary: Professional summary or objective statement.
        metadata: Processing lifecycle and source metadata.
    """

    id: UUID = Field(default_factory=uuid4)
    name: PersonName = Field(default_factory=PersonName)
    contact: ContactInformation | None = None
    skills: list[Skill] = []
    experience: list[Experience] = []
    education: list[Education] = []
    certifications: list[Certification] = []
    projects: list[Project] = []
    organizations: list[Organization] = []
    summary: str = ""
    metadata: ProcessingMetadata | None = None
