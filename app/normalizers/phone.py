"""
Phone number normalizer.

Normalizes phone numbers into a consistent format by stripping
non-digit characters and formatting with standard separators.
Aims for E.164-like format where possible.
"""

import re

from app.normalizers.base import BaseNormalizer


class PhoneNormalizer(BaseNormalizer):
    """
    Normalizes phone numbers into a consistent format.

    Handles common formats:
        - (555) 123-4567 → +15551234567
        - +1-555-123-4567 → +15551234567
        - 555.123.4567 → +15551234567
        - 1234567890 → +11234567890
        - +44 20 7946 0958 → +442079460958

    Rules:
        - Strip all non-digit/non-plus characters
        - If 10 digits (US), prepend +1
        - If 11+ digits starting with country code, prepend +
        - Preserve international format if + is present
    """

    def normalize(self, value: str) -> str:
        """
        Normalize a phone number string.

        Args:
            value: Raw phone number string.

        Returns:
            Normalized phone number in E.164-like format,
            or the original stripped value if format is unclear.
        """
        if not value or not value.strip():
            return ""

        # Strip everything except digits and leading +
        stripped = value.strip()
        has_plus = stripped.startswith("+")

        # Extract only digits
        digits = re.sub(r"[^\d]", "", stripped)

        if not digits:
            return value.strip()

        # US number: 10 digits → +1XXXXXXXXXX
        if len(digits) == 10:
            return f"+1{digits}"

        # Already has country code: 11+ digits
        if len(digits) >= 11:
            return f"+{digits}"

        # Short numbers or ambiguous — return with + if originally had it
        if has_plus:
            return f"+{digits}"

        return digits
