"""
Project entity.

Represents a project — personal, academic, or professional —
that a candidate has worked on. Projects can be associated with
a specific Experience or listed independently at the Candidate level.
"""

from app.domain.models.base import BaseEntity
from app.domain.models.partial_date import PartialDate


class Project(BaseEntity):
    """
    A project the candidate contributed to.

    Entity — each project has a unique identity. Projects can
    be associated with a specific Experience or listed
    independently at the Candidate level.

    Attributes:
        name: Project name.
        description: Brief description of the project.
        url: Link to the project (repository, demo, or site).
        technologies: List of technologies or tools used.
        start_date: Project start date (partial precision).
        end_date: Project end date. None if ongoing.
        is_current: Whether the project is still active.
    """

    name: str
    description: str = ""
    url: str | None = None
    technologies: list[str] = []
    start_date: PartialDate | None = None
    end_date: PartialDate | None = None
    is_current: bool = False
