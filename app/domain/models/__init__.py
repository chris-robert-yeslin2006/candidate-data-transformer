"""Canonical data models for candidate information."""

from app.domain.models.base import BaseEntity, BaseValueObject
from app.domain.models.candidate import CanonicalCandidate
from app.domain.models.certification import Certification
from app.domain.models.confidence import Confidence
from app.domain.models.contact import (
    ContactInformation,
    Email,
    Phone,
    SocialLink,
    SocialPlatform,
)
from app.domain.models.education import Education
from app.domain.models.experience import Experience
from app.domain.models.location import Location
from app.domain.models.metadata import ProcessingMetadata
from app.domain.models.organization import Organization
from app.domain.models.partial_date import PartialDate
from app.domain.models.person_name import PersonName
from app.domain.models.project import Project
from app.domain.models.provenance import (
    SOURCE_TYPE_ATS_JSON,
    SOURCE_TYPE_CSV,
    SOURCE_TYPE_GITHUB,
    SOURCE_TYPE_GREENHOUSE,
    SOURCE_TYPE_INDEED,
    SOURCE_TYPE_LEVER,
    SOURCE_TYPE_LINKEDIN,
    SOURCE_TYPE_NAUKRI,
    SOURCE_TYPE_PDF_RESUME,
    SOURCE_TYPE_SUCCESSFACTORS,
    SOURCE_TYPE_TXT_NOTES,
    SOURCE_TYPE_WORKDAY,
    Provenance,
    Provenanced,
)
from app.domain.models.skill import Skill
from app.domain.models.warning import Warning as ProcessingWarning

__all__ = [
    "BaseEntity",
    "BaseValueObject",
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
    "SOURCE_TYPE_CSV",
    "SOURCE_TYPE_ATS_JSON",
    "SOURCE_TYPE_PDF_RESUME",
    "SOURCE_TYPE_TXT_NOTES",
    "SOURCE_TYPE_LINKEDIN",
    "SOURCE_TYPE_GITHUB",
    "SOURCE_TYPE_WORKDAY",
    "SOURCE_TYPE_GREENHOUSE",
    "SOURCE_TYPE_LEVER",
    "SOURCE_TYPE_SUCCESSFACTORS",
    "SOURCE_TYPE_NAUKRI",
    "SOURCE_TYPE_INDEED",
]
