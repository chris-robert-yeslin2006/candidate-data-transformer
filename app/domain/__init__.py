"""
Domain layer — enterprise business rules.

Contains the canonical data model (CanonicalCandidate), value objects
(PersonName, Email, Phone, Skill, Location, SocialLink, PartialDate),
entities (Experience, Education, Certification, Project, Organization),
and metadata types (Provenance, Provenanced, Confidence,
ProcessingMetadata, ProcessingWarning).

No framework, I/O, or infrastructure imports here.
"""

from app.domain.models import (
    CanonicalCandidate,
    Certification,
    Confidence,
    ContactInformation,
    Education,
    Email,
    Experience,
    Location,
    Organization,
    PartialDate,
    PersonName,
    Phone,
    ProcessingMetadata,
    ProcessingWarning,
    Project,
    Provenance,
    Provenanced,
    Skill,
    SocialLink,
    SocialPlatform,
)

__all__ = [
    "CanonicalCandidate",
    "Certification",
    "Confidence",
    "ContactInformation",
    "Education",
    "Email",
    "Experience",
    "Location",
    "Organization",
    "PartialDate",
    "PersonName",
    "Phone",
    "ProcessingMetadata",
    "ProcessingWarning",
    "Project",
    "Provenance",
    "Provenanced",
    "Skill",
    "SocialLink",
    "SocialPlatform",
]
