"""
Abstract base normalizer interface.

All field-specific normalizers inherit from BaseNormalizer and
implement the normalize method. This establishes a consistent
contract for all normalization operations.
"""

from abc import ABC, abstractmethod


class BaseNormalizer(ABC):
    """
    Abstract base for field-specific normalizers.

    Each normalizer transforms raw field values into a consistent,
    standardised format. Normalizers are stateless and deterministic.
    """

    @abstractmethod
    def normalize(self, value: str) -> str:
        """
        Normalize a raw field value.

        Args:
            value: Raw value to normalize.

        Returns:
            Normalized value string.
        """
        ...
