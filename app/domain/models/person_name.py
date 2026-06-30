"""
PersonName value object.

Represents a candidate's name with structured components to
handle diverse international naming conventions — Western,
East Asian, Arabic, Spanish, and other formats where name
structure varies significantly.
"""

from pydantic import Field

from app.domain.models.base import BaseValueObject


class PersonName(BaseValueObject):
    """
    Structured personal name supporting international conventions.

    All fields are optional to support partial name data from
    any source. The ``display_name`` field preserves the original
    formatted name as extracted, while structured components
    enable culture-aware formatting for different output schemas.

    Attributes:
        prefix: Honorific or title (Mr., Dr., Ms., etc.).
        first: Given name or first name.
        middle: Middle name or middle initial.
        last: Family name or surname.
        suffix: Generational or professional suffix (Jr., III, Ph.D.).
        display_name: Full name as it should typically be displayed.
    """

    prefix: str = Field(default="", description="Honorific or title")
    first: str = Field(default="", description="Given name")
    middle: str = Field(default="", description="Middle name or initial")
    last: str = Field(default="", description="Family name or surname")
    suffix: str = Field(default="", description="Generational or professional suffix")
    display_name: str = Field(
        default="",
        description="Full formatted display name",
    )
