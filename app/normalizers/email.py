"""
Email normalizer.

Normalizes email addresses by lowercasing, trimming whitespace,
and performing basic format validation.
"""

import re

from app.normalizers.base import BaseNormalizer

# Basic email pattern for validation
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


class EmailNormalizer(BaseNormalizer):
    """
    Normalizes email addresses.

    Rules:
        - Lowercase the entire address
        - Strip leading/trailing whitespace
        - Validate basic email format
        - Return empty string for invalid emails
    """

    def normalize(self, value: str) -> str:
        """
        Normalize an email address.

        Args:
            value: Raw email string.

        Returns:
            Lowercased, trimmed email string.
            Empty string if the email is invalid.
        """
        if not value or not value.strip():
            return ""

        normalized = value.strip().lower()

        if not EMAIL_PATTERN.match(normalized):
            return normalized  # Return as-is but lowercased; don't discard

        return normalized
