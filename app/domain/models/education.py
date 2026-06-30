"""
Education value object.

Represents a single education entry within a candidate's profile.

TODO: Add degree type enum and date parsing in Phase 2.
"""

from pydantic import BaseModel


class Education(BaseModel):
    """
    A single education entry.

    Attributes:
        institution: School or university name.
        degree: Degree or qualification name.
        field: Field of study (e.g. "Computer Science").
        start_date: Start date string (to be normalised).
        end_date: End date string or empty for ongoing.
    """

    institution: str = ""
    degree: str = ""
    field: str = ""
    start_date: str = ""
    end_date: str = ""
