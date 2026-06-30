"""
Name normalizer.

Normalizes candidate names by applying title case, stripping
extra whitespace, and trimming leading/trailing spaces.
"""

import re

from app.normalizers.base import BaseNormalizer


class NameNormalizer(BaseNormalizer):
    """
    Normalizes person names.

    Rules:
        - Title-case each word (John Doe)
        - Collapse multiple spaces into single space
        - Strip leading/trailing whitespace
        - Preserve hyphenated names (Mary-Jane → Mary-Jane)
        - Handle all-caps and all-lowercase input
    """

    def normalize(self, value: str) -> str:
        """
        Normalize a name string.

        Args:
            value: Raw name string.

        Returns:
            Title-cased, whitespace-normalized name.
        """
        if not value or not value.strip():
            return ""

        # Collapse multiple whitespace into single spaces
        normalized = re.sub(r"\s+", " ", value.strip())

        # Title-case, handling hyphens properly
        parts = normalized.split(" ")
        title_parts: list[str] = []
        for part in parts:
            if "-" in part:
                # Title-case each hyphenated segment
                sub_parts = part.split("-")
                title_parts.append(
                    "-".join(sp.capitalize() for sp in sub_parts)
                )
            else:
                title_parts.append(part.capitalize())

        return " ".join(title_parts)
