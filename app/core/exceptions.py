"""
Application exception hierarchy.

All pipeline-specific exceptions inherit from CandidateTransformerError,
allowing callers to catch a base type while retaining granularity
for specific error handling.
"""

from typing import Any


class CandidateTransformerError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """
        Initialize the error with a message and optional context.

        Args:
            message: Human-readable error description.
            details: Optional structured context for debugging.
        """
        self.details = details or {}
        super().__init__(message)


class ConfigurationError(CandidateTransformerError):
    """Raised when application configuration is invalid or missing."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """
        Initialize configuration error.

        Args:
            message: Description of the configuration issue.
            field: Name of the misconfigured field, if applicable.
        """
        details = {"field": field} if field else None
        super().__init__(message, details=details)


class ParsingError(CandidateTransformerError):
    """Raised when a parser fails to process input data."""

    def __init__(self, message: str, source_type: str | None = None) -> None:
        """
        Initialize parsing error.

        Args:
            message: Description of the parsing failure.
            source_type: The source type that failed, if known.
        """
        details = {"source_type": source_type} if source_type else None
        super().__init__(message, details=details)


class ValidationError(CandidateTransformerError):
    """Raised when output validation fails against a target schema."""

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None) -> None:
        """
        Initialize validation error.

        Args:
            message: Description of the validation failure.
            errors: List of structured validation error details.
        """
        details = {"validation_errors": errors} if errors else None
        super().__init__(message, details=details)


class PipelineError(CandidateTransformerError):
    """Raised when the pipeline encounters an unrecoverable error."""

    def __init__(self, message: str, stage: str | None = None) -> None:
        """
        Initialize pipeline error.

        Args:
            message: Description of the pipeline failure.
            stage: The pipeline stage where the failure occurred.
        """
        details = {"stage": stage} if stage else None
        super().__init__(message, details=details)
