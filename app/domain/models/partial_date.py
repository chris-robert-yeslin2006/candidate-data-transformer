"""
PartialDate value object.

Represents dates where only partial information is available —
common in resumes and profiles where months or days are omitted.
Supports three precision levels: year-only, year+month, and full
date. Enables date comparison and ordering even with partial data.
"""

from pydantic import Field

from app.domain.models.base import BaseValueObject


class PartialDate(BaseValueObject):
    """
    A date with potentially partial precision.

    Designed for resume and profile data where dates like "2022",
    "Jan 2022", or "2022-01-15" are common. Each component is
    optional, allowing any level of granularity. Validation ensures
    that if a component is provided, all more-significant components
    are also present (e.g., day requires month and year).

    Attributes:
        year: Year component (required for any meaningful date).
        month: Month component (1-12). Optional.
        day: Day component (1-31). Optional.
    """

    year: int | None = Field(default=None, description="Year")
    month: int | None = Field(default=None, description="Month (1-12)")
    day: int | None = Field(default=None, description="Day (1-31)")
