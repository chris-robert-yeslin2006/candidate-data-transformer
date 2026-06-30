"""
Contact information models.

Aggregates all contact methods (email, phone, social links, location)
into a single ContactInformation value object. Each contact method
is modeled as a distinct value object with its own validation.
"""

from enum import StrEnum

from app.domain.models.base import BaseValueObject
from app.domain.models.location import Location


class SocialPlatform(StrEnum):
    """
    Supported social media and web presence platforms.

    StrEnum enables clean JSON serialization — values are plain
    strings rather than enum objects. Adding a new platform
    requires only adding a member to this enum.
    """

    LINKEDIN = "linkedin"
    GITHUB = "github"
    TWITTER = "twitter"
    STACK_OVERFLOW = "stack_overflow"
    MEDIUM = "medium"
    PERSONAL_WEBSITE = "personal_website"
    OTHER = "other"


class Email(BaseValueObject):
    """
    Email address with type classification.

    Attributes:
        value: The email address string (validated by Pydantic).
        type: Classification (personal, work, other).
        is_primary: Whether this is the primary email.
    """

    value: str = ""
    type: str = ""
    is_primary: bool = False


class Phone(BaseValueObject):
    """
    Phone number with type classification.

    Attributes:
        value: The phone number string (raw; normalizer handles formatting).
        type: Classification (mobile, work, home, fax, other).
        is_primary: Whether this is the primary phone number.
    """

    value: str = ""
    type: str = ""
    is_primary: bool = False


class SocialLink(BaseValueObject):
    """
    Social media or web presence link.

    Attributes:
        platform: The platform enum value.
        url: Full URL to the profile.
        username: The username or handle on the platform.
    """

    platform: SocialPlatform
    url: str = ""
    username: str = ""


class ContactInformation(BaseValueObject):
    """
    Aggregate of all contact methods for a candidate.

    Groups email, phone, social links, and location into one
    composable value object. Owned by the Candidate aggregate.

    Attributes:
        emails: List of email addresses.
        phones: List of phone numbers.
        social_links: List of social media profiles.
        location: Primary physical location.
    """

    emails: list[Email] = []
    phones: list[Phone] = []
    social_links: list[SocialLink] = []
    location: Location | None = None
