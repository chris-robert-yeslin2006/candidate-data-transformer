"""
Location value object.

Represents a physical location with structured components.
Supports both fully parsed addresses and raw unparsed text.
"""

from app.domain.models.base import BaseValueObject


class Location(BaseValueObject):
    """
    Physical location with structured address components.

    Designed to represent any level of address specificity.
    All fields are optional to support partial address data
    from any source. The ``raw`` field preserves the original
    unparsed address string when structured parsing is not
    possible or desired.

    Attributes:
        street: Street address including number and name.
        city: City or locality name.
        state: State, province, or region.
        postal_code: ZIP or postal code.
        country: Country name or ISO code.
        raw: Original unparsed address text.
    """

    street: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""
    raw: str = ""
