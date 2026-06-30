"""
Normalization layer.

Provides field-specific normalizers (phone, email, name) and
the NormalizationService that applies them to candidate data.
"""

from app.normalizers.base import BaseNormalizer
from app.normalizers.email import EmailNormalizer
from app.normalizers.name import NameNormalizer
from app.normalizers.normalization_service import NormalizationService
from app.normalizers.phone import PhoneNormalizer

__all__ = [
    "BaseNormalizer",
    "EmailNormalizer",
    "NameNormalizer",
    "NormalizationService",
    "PhoneNormalizer",
]
