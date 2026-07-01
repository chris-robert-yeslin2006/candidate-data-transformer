"""
ColumnRule — a typed, extensible alternative to flat column name mapping.

Each ColumnRule declares the canonical field path, the expected
value type, whether the column is required, and an optional
transform function. This replaces the flat ``DEFAULT_COLUMN_MAPPING``
dict with structured, introspectable rules.

Tech Debt #2: ColumnRule adoption is the replacement for the
flat dict-based mapping in candidate_mapper.py.
"""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, Field

from app.domain.models.warning import Warning as ProcessingWarning

TransformFunc = Callable[[str], Any]


class ColumnRule(BaseModel):
    """
    A typed mapping rule from a source column to a canonical field.

    Each rule describes how a single source column (e.g. CSV header,
    JSON key) maps to a canonical model field path, along with
    type information, requiredness, and an optional transform.

    Attributes:
        field: Canonical field path (e.g. ``name.display_name``).
        type_hint: Expected Python type (str, int, list, etc.).
        required: If True, a missing value produces a warning.
        default: Default value when the column is absent.
        transform: Optional callable to transform the raw value.
        description: Human-readable purpose of this field.
        aliases: Alternative source column names (case-insensitive).
    """

    field: str
    type_hint: type = str
    required: bool = False
    default: Any = ""
    transform: TransformFunc | None = None
    description: str = ""
    aliases: list[str] = Field(default_factory=list)

    def apply(
        self,
        raw_value: str | None,
        warnings: list[ProcessingWarning] | None = None,
    ) -> Any:
        """
        Apply this rule to a raw source value.

        Handles missing values (uses default), type coercion, and
        optional transform functions. Appends a warning if a
        required column is missing.

        Args:
            raw_value: The raw string value from the source, or None
                       if the column is absent.
            warnings: Optional accumulator list for processing warnings.

        Returns:
            The processed (and optionally transformed) value.
        """
        if warnings is None:
            warnings = []

        if raw_value is None or not raw_value.strip():
            if self.required and self.default == "":
                warnings.append(
                    ProcessingWarning(
                        message=f"Required column '{self.field}' is missing",
                        source="column_rule",
                        code="MISSING_REQUIRED_COLUMN",
                        field=self.field,
                    )
                )
            return self.default

        value: Any = raw_value.strip()

        if self.transform is not None:
            try:
                value = self.transform(value)
            except (ValueError, TypeError) as exc:
                warnings.append(
                    ProcessingWarning(
                        message=f"Transform failed for column '{self.field}': {exc}",
                        source="column_rule",
                        code="TRANSFORM_ERROR",
                        field=self.field,
                    )
                )
                return self.default

        return value
