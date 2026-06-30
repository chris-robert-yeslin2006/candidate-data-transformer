"""
Organization entity.

Represents an organization — an employer, volunteer body, or
professional association. Used standalone for non-employment
involvements and referenced by Experience for work history.
"""

from app.domain.models.base import BaseEntity
from app.domain.models.location import Location
from app.domain.models.partial_date import PartialDate


class Organization(BaseEntity):
    """
    Organizational involvement outside of employment.

    Entity — each organization entry has a unique identity.
    Covers employer companies, volunteer roles, board memberships,
    professional associations, and community participation.
    Referenced by Experience for employment history.

    Attributes:
        name: Organization name.
        role: Role or position held.
        location: Geographic location of the organization.
        start_date: Start date of involvement (partial precision).
        end_date: End date of involvement. None if ongoing.
        description: Description of the organization or
                     responsibilities.
        is_current: Whether the candidate is currently involved.
    """

    name: str
    role: str = ""
    location: Location | None = None
    start_date: PartialDate | None = None
    end_date: PartialDate | None = None
    description: str = ""
    is_current: bool = False
