"""
Experience value object.

Represents a single work experience entry within a candidate's profile.

TODO: Add date parsing and validation in Phase 2.
"""

from pydantic import BaseModel


class Experience(BaseModel):
    """
    A single work experience entry.

    Attributes:
        title: Job title or position.
        company: Employer name.
        start_date: Start date string (to be normalised).
        end_date: End date string or empty for current.
        description: Free-text description of responsibilities.
    """

    title: str = ""
    company: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""
