"""
Certification entity.

Represents a professional certification, license, or
accreditation held by a candidate.
"""

from app.domain.models.base import BaseEntity
from app.domain.models.partial_date import PartialDate


class Certification(BaseEntity):
    """
    A professional certification or license.

    Entity — each certification has a unique identity. Supports
    the full lifecycle from issuance through expiration.

    Attributes:
        name: Certification or license name.
        issuer: Organization that issued the certification.
        obtained_date: Date the certification was obtained
                       (partial precision).
        url: Link to the certification or verification page.
        expires: Expiration date. None if no expiration.
        credential_id: Unique credential identifier from the issuer.
    """

    name: str
    issuer: str = ""
    obtained_date: PartialDate | None = None
    url: str | None = None
    expires: PartialDate | None = None
    credential_id: str = ""
