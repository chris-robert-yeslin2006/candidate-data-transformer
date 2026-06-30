"""
Abstract base parser interface.

All source-specific parsers inherit from BaseParser and implement
the parse method. This establishes a consistent contract: every
parser accepts raw data and returns a canonical model with metadata.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.domain.models import CanonicalCandidate

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """
    Abstract base for all source-specific parsers.

    Every parser must implement ``parse()``, which converts raw input
    data into a canonical candidate model. Parsers encode format-
    specific extraction logic but never leak format-specific types
    into downstream services.
    """

    @abstractmethod
    def parse(self, raw_data: str | bytes, **kwargs: Any) -> CanonicalCandidate:
        """
        Parse raw input data into a canonical candidate structure.

        Args:
            raw_data: Raw input content (string for text formats,
                      bytes for binary formats like PDF).
            **kwargs: Optional format-specific parameters.

        Returns:
            CanonicalCandidate representing the parsed candidate.

        Raises:
            ParsingError: If the input cannot be parsed.
        """
        ...
