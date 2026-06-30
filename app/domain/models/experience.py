"""
Experience entity.

Represents a single work experience entry within a candidate's profile.
References an Organization for the employer and Skill entities for
technologies used.
"""

from pydantic import Field

from app.domain.models.base import BaseEntity
from app.domain.models.location import Location
from app.domain.models.organization import Organization
from app.domain.models.partial_date import PartialDate
from app.domain.models.project import Project
from app.domain.models.skill import Skill


class Experience(BaseEntity):
    """
    A single work experience entry.

    Entity — each experience entry has a unique identity. References
    an Organization for the employer to avoid duplicating company
    information across entries. Uses Skill entities for technologies
    used, enabling cross-referencing and deduplication.

    Attributes:
        title: Job title or position held.
        organization: Employer or organization (reuses Organization model).
        location: Geographic location of the role.
        start_date: Start date of employment (partial precision).
        end_date: End date of employment. None if current.
        description: Free-text description of responsibilities.
        is_current: Whether the candidate currently holds this role.
        projects: List of projects undertaken during this role.
        skills_used: Skills and technologies used in this role.
    """

    title: str = ""
    organization: Organization | None = Field(
        default=None,
        description="Employer or organization",
    )
    location: Location | None = None
    start_date: PartialDate | None = None
    end_date: PartialDate | None = None
    description: str = ""
    is_current: bool = False
    projects: list[Project] = []
    skills_used: list[Skill] = []
