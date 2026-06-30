"""
Education entity.

Represents a single education entry within a candidate's profile.
Each entry is uniquely identified and contains institution, degree,
and date range information.
"""

from pydantic import Field

from app.domain.models.base import BaseEntity
from app.domain.models.location import Location
from app.domain.models.partial_date import PartialDate


class Education(BaseEntity):
    """
    A single education entry.

    Entity — each education entry has a unique identity. Two
    entries with the same institution and degree are distinct
    if they have different IDs.

    Attributes:
        institution: School or university name.
        degree: Degree or qualification name.
        field: Field of study (e.g. "Computer Science").
        location: Geographic location of the institution.
        start_date: Start date of attendance (partial precision).
        end_date: End date of attendance. None if ongoing.
        gpa: Grade point average, if available.
        is_current: Whether the candidate is currently enrolled.
    """

    institution: str = ""
    degree: str = ""
    field: str = ""
    location: Location | None = None
    start_date: PartialDate | None = None
    end_date: PartialDate | None = None
    gpa: float | None = Field(default=None, ge=0.0, le=4.0)
    is_current: bool = False
