"""
Normalization service.

Applies all field-specific normalizers to a CanonicalCandidate,
transforming raw values into consistent, standardised formats.
"""

from __future__ import annotations

import logging

from app.domain.models import CanonicalCandidate
from app.domain.models.warning import Warning as ProcessingWarning
from app.normalizers.email import EmailNormalizer
from app.normalizers.name import NameNormalizer
from app.normalizers.phone import PhoneNormalizer

logger = logging.getLogger(__name__)


class NormalizationService:
    """
    Applies normalizers to a CanonicalCandidate.

    Normalizes name, email, and phone fields using dedicated
    normalizers. Returns the candidate with normalized values
    and a list of any warnings generated during normalization.
    """

    def __init__(self) -> None:
        """Initialize the normalization service with all field normalizers."""
        self._phone_normalizer = PhoneNormalizer()
        self._email_normalizer = EmailNormalizer()
        self._name_normalizer = NameNormalizer()
        logger.debug("NormalizationService initialized")

    def normalize(
        self,
        candidate: CanonicalCandidate,
    ) -> tuple[CanonicalCandidate, list[ProcessingWarning]]:
        """
        Normalize all fields on a CanonicalCandidate.

        Normalizes:
            - name.display_name, name.first, name.last, name.middle
            - contact.emails[*].value
            - contact.phones[*].value

        Args:
            candidate: The candidate to normalize.

        Returns:
            Tuple of (normalized candidate, list of warnings).
        """
        warnings: list[ProcessingWarning] = []

        # Normalize name fields
        self._normalize_name(candidate, warnings)

        # Normalize contact fields
        self._normalize_contact(candidate, warnings)

        return candidate, warnings

    def _normalize_name(
        self,
        candidate: CanonicalCandidate,
        warnings: list[ProcessingWarning],
    ) -> None:
        """Normalize name fields on the candidate."""
        if candidate.name:
            if candidate.name.display_name:
                candidate.name.display_name = self._name_normalizer.normalize(
                    candidate.name.display_name
                )
            if candidate.name.first:
                candidate.name.first = self._name_normalizer.normalize(
                    candidate.name.first
                )
            if candidate.name.last:
                candidate.name.last = self._name_normalizer.normalize(
                    candidate.name.last
                )
            if candidate.name.middle:
                candidate.name.middle = self._name_normalizer.normalize(
                    candidate.name.middle
                )

    def _normalize_contact(
        self,
        candidate: CanonicalCandidate,
        warnings: list[ProcessingWarning],
    ) -> None:
        """Normalize contact fields on the candidate."""
        if not candidate.contact:
            return

        for email in candidate.contact.emails:
            if email.value:
                original = email.value
                email.value = self._email_normalizer.normalize(email.value)
                if email.value != original:
                    logger.debug(
                        "Normalized email '%s' -> '%s'", original, email.value
                    )

        for phone in candidate.contact.phones:
            if phone.value:
                original = phone.value
                phone.value = self._phone_normalizer.normalize(phone.value)
                if phone.value != original:
                    logger.debug(
                        "Normalized phone '%s' -> '%s'", original, phone.value
                    )
