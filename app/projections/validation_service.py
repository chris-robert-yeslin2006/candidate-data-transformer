"""
Schema validation service.

Validates projected output against a target schema before delivery.
Catches projection misconfiguration, missing required fields, and
type mismatches.
"""

from __future__ import annotations

import logging
from typing import Any

from app.domain.models.warning import Warning as ProcessingWarning

logger = logging.getLogger(__name__)

# Default required fields in the output
DEFAULT_REQUIRED_FIELDS = ["full_name"]


class ValidationService:
    """
    Validates projected output against a target schema.

    Checks:
        - Required fields are present and non-empty
        - Field types match expectations
        - Returns structured validation errors
    """

    def validate(
        self,
        output: dict[str, Any],
        schema: dict[str, Any] | None = None,
    ) -> tuple[bool, list[ProcessingWarning]]:
        """
        Validate projected output against a target schema.

        Args:
            output: The projected output dictionary.
            schema: Optional schema definition with:
                - required: list of required field names
                - types: dict mapping field names to expected types

        Returns:
            Tuple of (is_valid, list of validation warnings).
        """
        warnings: list[ProcessingWarning] = []
        is_valid = True

        if schema is None:
            schema = {
                "required": DEFAULT_REQUIRED_FIELDS,
            }

        # Check required fields
        required_fields = schema.get("required", [])
        for field_name in required_fields:
            if field_name not in output:
                is_valid = False
                warnings.append(
                    ProcessingWarning(
                        message=f"Required field '{field_name}' is missing from output",
                        source="validation_service",
                        code="MISSING_REQUIRED_FIELD",
                        field=field_name,
                    )
                )
            elif output[field_name] is None or (
                isinstance(output[field_name], str) and not output[field_name].strip()
            ):
                is_valid = False
                warnings.append(
                    ProcessingWarning(
                        message=f"Required field '{field_name}' is empty",
                        source="validation_service",
                        code="EMPTY_REQUIRED_FIELD",
                        field=field_name,
                    )
                )

        # Check type constraints
        type_constraints = schema.get("types", {})
        type_map = {
            "string": str,
            "str": str,
            "list": list,
            "array": list,
            "dict": dict,
            "object": dict,
            "int": int,
            "integer": int,
            "float": float,
            "number": (int, float),
            "bool": bool,
            "boolean": bool,
        }

        for field_name, expected_type_str in type_constraints.items():
            if field_name not in output:
                continue

            expected_type = type_map.get(expected_type_str.lower())
            if expected_type and not isinstance(output[field_name], expected_type):
                is_valid = False
                warnings.append(
                    ProcessingWarning(
                        message=(
                            f"Field '{field_name}' expected type '{expected_type_str}' "
                            f"but got '{type(output[field_name]).__name__}'"
                        ),
                        source="validation_service",
                        code="TYPE_MISMATCH",
                        field=field_name,
                    )
                )

        return is_valid, warnings
