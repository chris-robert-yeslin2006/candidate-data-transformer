"""
Projection engine.

Transforms the canonical candidate model into client-specific
output schemas at runtime based on a projection configuration.
Configuration-driven, no code changes for new client schemas.
"""

from __future__ import annotations

import logging
from typing import Any

from app.domain.models import CanonicalCandidate
from app.domain.models.warning import Warning as ProcessingWarning

logger = logging.getLogger(__name__)

# Default projection configuration — maps canonical fields to
# a standard output schema with common naming conventions.
DEFAULT_PROJECTION_CONFIG: dict[str, Any] = {
    "fields": {
        "full_name": "name.display_name",
        "first_name": "name.first",
        "last_name": "name.last",
        "email": "contact.emails[0].value",
        "phone": "contact.phones[0].value",
        "skills": "skills[*].name",
        "summary": "summary",
        "experience": "experience",
        "education": "education",
    },
}


class ProjectionService:
    """
    Transforms canonical candidate data into client-specific output.

    Accepts a projection configuration that specifies:
    - Field mappings (rename canonical fields)
    - Transforms (format conversions)
    - Defaults (fallback values)
    """

    def project(
        self,
        candidate: CanonicalCandidate,
        config: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], list[ProcessingWarning]]:
        """
        Project a CanonicalCandidate into the target output schema.

        Args:
            candidate: The canonical candidate to project.
            config: Projection configuration. Uses default if None.

        Returns:
            Tuple of (projected dictionary, list of warnings).
        """
        warnings: list[ProcessingWarning] = []
        projection_config = config or DEFAULT_PROJECTION_CONFIG
        field_mappings = projection_config.get("fields", {})
        defaults = projection_config.get("defaults", {})

        result: dict[str, Any] = {}

        for output_key, source_path in field_mappings.items():
            value = self._resolve_path(candidate, source_path)

            if value is None and output_key in defaults:
                value = defaults[output_key]

            if value is not None:
                result[output_key] = value

        return result, warnings

    def _resolve_path(
        self,
        candidate: CanonicalCandidate,
        path: str,
    ) -> Any:
        """
        Resolve a dot-path against a CanonicalCandidate.

        Supports:
            - Simple paths: "summary"
            - Nested paths: "name.display_name"
            - Array access: "contact.emails[0].value"
            - Wildcard arrays: "skills[*].name"
            - Complex objects: "experience", "education"

        Args:
            candidate: Source candidate.
            path: Dot-delimited path string.

        Returns:
            Resolved value, or None if not found.
        """
        if path == "summary":
            return candidate.summary or None

        if path == "name.display_name":
            return candidate.name.display_name or None

        if path == "name.first":
            return candidate.name.first or None

        if path == "name.last":
            return candidate.name.last or None

        if path == "name.middle":
            return candidate.name.middle or None

        if path == "contact.emails[0].value":
            if candidate.contact and candidate.contact.emails:
                return candidate.contact.emails[0].value or None
            return None

        if path == "contact.phones[0].value":
            if candidate.contact and candidate.contact.phones:
                return candidate.contact.phones[0].value or None
            return None

        if path == "skills[*].name":
            if candidate.skills:
                return [s.name for s in candidate.skills]
            return None

        if path == "experience":
            if candidate.experience:
                return [
                    {
                        "title": exp.title,
                        "company": exp.organization.name if exp.organization else "",
                        "description": exp.description,
                    }
                    for exp in candidate.experience
                ]
            return None

        if path == "education":
            if candidate.education:
                return [
                    {
                        "institution": edu.institution,
                        "degree": edu.degree,
                        "field": edu.field,
                    }
                    for edu in candidate.education
                ]
            return None

        if path == "contact.location":
            if candidate.contact and candidate.contact.location:
                loc = candidate.contact.location
                return {
                    "city": loc.city,
                    "state": loc.state,
                    "country": loc.country,
                    "raw": loc.raw,
                }
            return None

        # Generic nested path resolution via model_dump
        try:
            data = candidate.model_dump()
            parts = path.split(".")
            current: Any = data
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return None
                if current is None:
                    return None
            return current
        except Exception:
            return None
