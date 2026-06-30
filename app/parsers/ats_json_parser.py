"""
ATS JSON source parser.

Handles structured candidate data in JSON format, typically exported
from Applicant Tracking Systems. Maps JSON keys to canonical field
names using a configurable mapping.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from app.core.exceptions import ParsingError
from app.domain.models import (
    CanonicalCandidate,
    ContactInformation,
    Education,
    Email,
    Experience,
    Phone,
    Skill,
)
from app.domain.models.metadata import ProcessingMetadata
from app.domain.models.organization import Organization
from app.domain.models.person_name import PersonName
from app.domain.models.provenance import SourceType
from app.domain.models.warning import Warning as ProcessingWarning
from app.parsers.base import BaseParser

logger = logging.getLogger(__name__)

# Default mapping from JSON keys to canonical field paths.
# Supports common ATS export formats (Greenhouse, Lever, Workday, etc.)
DEFAULT_JSON_KEY_MAPPING: dict[str, str] = {
    "name": "name.display_name",
    "full_name": "name.display_name",
    "first_name": "name.first",
    "last_name": "name.last",
    "middle_name": "name.middle",
    "email": "contact.email",
    "email_address": "contact.email",
    "phone": "contact.phone",
    "phone_number": "contact.phone",
    "mobile": "contact.phone",
    "skills": "skills",
    "title": "experience.title",
    "job_title": "experience.title",
    "current_title": "experience.title",
    "company": "experience.company",
    "current_company": "experience.company",
    "experience": "experience.description",
    "work_experience": "experience_list",
    "education": "education_list",
    "summary": "summary",
    "objective": "summary",
    "location": "contact.location",
    "address": "contact.location",
    "city": "contact.city",
    "state": "contact.state",
    "country": "contact.country",
}


class AtsJsonParser(BaseParser):
    """
    Parser for JSON-encoded candidate data from ATS exports.

    Reads JSON content, maps keys to canonical model fields, and
    returns a structured candidate representation. Supports optional
    key remapping for different ATS export formats.

    Handles:
        - Flat JSON objects with candidate fields
        - Nested JSON structures (experience, education as lists)
        - Missing/optional keys (defaults to empty)
        - Case-insensitive key matching
        - Malformed JSON with clear error messages
    """

    source_type: SourceType = SourceType.ATS_JSON
    display_name: str = "ATS JSON Parser"
    supported_extensions: list[str] = [".json"]
    supported_mime_types: list[str] = ["application/json"]
    requires_ai: bool = False
    parser_version: str = "1.0.0"

    def __init__(
        self,
        key_mapping: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize the ATS JSON parser.

        Args:
            key_mapping: Optional override mapping from JSON keys
                        to canonical field paths.
        """
        self._key_mapping = DEFAULT_JSON_KEY_MAPPING if key_mapping is None else key_mapping
        logger.debug(
            "AtsJsonParser initialized with %d key mappings",
            len(self._key_mapping),
        )

    def parse(self, raw_data: str | bytes, **kwargs: Any) -> CanonicalCandidate:
        """
        Parse JSON content into a CanonicalCandidate.

        Args:
            raw_data: JSON content as a string or bytes.
            **kwargs:
                key_mapping: Optional per-call mapping override.
                source_id: Identifier for the source file.

        Returns:
            CanonicalCandidate with parsed fields.

        Raises:
            ParsingError: If the JSON data is malformed or empty.
        """
        key_mapping = kwargs.get("key_mapping", self._key_mapping)
        source_id = kwargs.get("source_id", "")
        warnings: list[ProcessingWarning] = []

        data = self._parse_json(raw_data)
        candidate = self._map_to_candidate(data, key_mapping, warnings)

        candidate.metadata = ProcessingMetadata(
            created_at=datetime.now(),
            updated_at=datetime.now(),
            parser_version=self.parser_version,
            source_types=[SourceType.ATS_JSON],
            warnings=warnings,
        )

        return candidate

    def _parse_json(self, raw_data: str | bytes) -> dict[str, Any]:
        """
        Parse and validate the JSON input.

        Args:
            raw_data: Raw JSON string or bytes.

        Returns:
            Parsed dictionary.

        Raises:
            ParsingError: If JSON is malformed or not a dict.
        """
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode("utf-8")

        raw_data = raw_data.strip()
        if not raw_data:
            raise ParsingError("JSON input is empty", source_type="ats_json")

        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            raise ParsingError(
                f"Malformed JSON: {exc}",
                source_type="ats_json",
            )

        if not isinstance(data, dict):
            raise ParsingError(
                f"Expected JSON object, got {type(data).__name__}",
                source_type="ats_json",
            )

        return data

    def _map_to_candidate(
        self,
        data: dict[str, Any],
        key_mapping: dict[str, str],
        warnings: list[ProcessingWarning],
    ) -> CanonicalCandidate:
        """
        Map a JSON dict to a CanonicalCandidate.

        Args:
            data: Parsed JSON dictionary.
            key_mapping: Mapping from JSON keys to canonical field paths.
            warnings: Warning accumulator.

        Returns:
            Populated CanonicalCandidate.
        """
        candidate = CanonicalCandidate()
        contact = ContactInformation()
        name = PersonName()
        raw_skills: list[str] = []
        experience_title = ""
        experience_company = ""
        experience_description = ""
        experience_list: list[dict[str, Any]] = []
        education_list: list[dict[str, Any]] = []

        # Build case-insensitive lookup from JSON keys
        lower_data: dict[str, Any] = {k.lower().strip(): v for k, v in data.items()}

        # Build case-insensitive lookup from key mapping
        lower_mapping: dict[str, str] = {k.lower().strip(): v for k, v in key_mapping.items()}

        matched_keys: set[str] = set()

        for json_key_lower, field_path in lower_mapping.items():
            if json_key_lower not in lower_data:
                continue

            value = lower_data[json_key_lower]
            matched_keys.add(json_key_lower)

            if value is None or (isinstance(value, str) and not value.strip()):
                continue

            if field_path == "name.display_name":
                if not name.display_name and isinstance(value, str):
                    name.display_name = value.strip()
            elif field_path == "name.first":
                if isinstance(value, str):
                    name.first = value.strip()
            elif field_path == "name.last":
                if isinstance(value, str):
                    name.last = value.strip()
            elif field_path == "name.middle":
                if isinstance(value, str):
                    name.middle = value.strip()
            elif field_path == "contact.email":
                if isinstance(value, str) and value.strip():
                    contact.emails = [Email(value=value.strip(), type="", is_primary=True)]
            elif field_path == "contact.phone":
                if isinstance(value, str) and value.strip():
                    contact.phones = [Phone(value=value.strip(), type="", is_primary=True)]
            elif field_path == "contact.location":
                from app.domain.models.location import Location
                if isinstance(value, str):
                    contact.location = Location(raw=value.strip())
                elif isinstance(value, dict):
                    contact.location = Location(
                        city=value.get("city", ""),
                        state=value.get("state", ""),
                        country=value.get("country", ""),
                        raw=value.get("raw", ""),
                    )
            elif field_path == "contact.city":
                from app.domain.models.location import Location
                if isinstance(value, str):
                    if contact.location is None:
                        contact.location = Location()
                    contact.location.city = value.strip()
            elif field_path == "contact.state":
                from app.domain.models.location import Location
                if isinstance(value, str):
                    if contact.location is None:
                        contact.location = Location()
                    contact.location.state = value.strip()
            elif field_path == "contact.country":
                from app.domain.models.location import Location
                if isinstance(value, str):
                    if contact.location is None:
                        contact.location = Location()
                    contact.location.country = value.strip()
            elif field_path == "skills":
                raw_skills = self._parse_skills(value)
            elif field_path == "experience.title":
                if isinstance(value, str):
                    experience_title = value.strip()
            elif field_path == "experience.company":
                if isinstance(value, str):
                    experience_company = value.strip()
            elif field_path == "experience.description":
                if isinstance(value, str):
                    experience_description = value.strip()
            elif field_path == "experience_list":
                if isinstance(value, list):
                    experience_list = value
            elif field_path == "education_list":
                if isinstance(value, list):
                    education_list = value
            elif field_path == "summary":
                if isinstance(value, str):
                    candidate.summary = value.strip()

        # Warn about unrecognized keys
        for key_lower in lower_data:
            if key_lower not in matched_keys:
                warnings.append(
                    ProcessingWarning(
                        message=f"Ignoring unknown JSON key '{key_lower}'",
                        source="ats_json_parser",
                        code="UNKNOWN_KEY",
                        field="",
                    )
                )

        # Assemble name
        candidate.name = name
        if not name.display_name and (name.first or name.last):
            parts = [name.first, name.middle, name.last]
            candidate.name.display_name = " ".join(p for p in parts if p)

        # Assemble contact
        if contact.emails or contact.phones or contact.location:
            candidate.contact = contact
        else:
            candidate.contact = None

        # Assemble skills
        candidate.skills = [
            Skill(name=s.strip()) for s in raw_skills if s.strip()
        ]

        # Assemble experience
        experiences: list[Experience] = []
        if experience_title or experience_company or experience_description:
            experiences.append(
                Experience(
                    title=experience_title,
                    organization=Organization(name=experience_company) if experience_company else None,
                    description=experience_description,
                )
            )
        for exp_dict in experience_list:
            if isinstance(exp_dict, dict):
                experiences.append(self._parse_experience_dict(exp_dict))
        candidate.experience = experiences

        # Assemble education
        candidate.education = [
            self._parse_education_dict(edu_dict)
            for edu_dict in education_list
            if isinstance(edu_dict, dict)
        ]

        return candidate

    def _parse_skills(self, value: Any) -> list[str]:
        """
        Parse skills from a JSON value.

        Supports:
            - List of strings: ["Python", "JavaScript"]
            - Comma-separated string: "Python, JavaScript"
            - List of dicts with 'name' key: [{"name": "Python"}]

        Args:
            value: Raw skill value from JSON.

        Returns:
            List of skill name strings.
        """
        if isinstance(value, list):
            skills: list[str] = []
            for item in value:
                if isinstance(item, str):
                    skills.append(item.strip())
                elif isinstance(item, dict) and "name" in item:
                    skills.append(str(item["name"]).strip())
            return skills
        elif isinstance(value, str):
            for delim in ["|", ";", ","]:
                if delim in value:
                    return [s.strip() for s in value.split(delim) if s.strip()]
            return [value.strip()] if value.strip() else []
        return []

    def _parse_experience_dict(self, data: dict[str, Any]) -> Experience:
        """
        Parse a single experience entry from a JSON dict.

        Args:
            data: Experience dictionary with keys like title, company, description.

        Returns:
            Experience entity.
        """
        title = str(data.get("title", data.get("job_title", ""))).strip()
        company = str(data.get("company", data.get("organization", data.get("employer", "")))).strip()
        description = str(data.get("description", data.get("summary", ""))).strip()

        org = Organization(name=company) if company else None

        return Experience(
            title=title,
            organization=org,
            description=description,
        )

    def _parse_education_dict(self, data: dict[str, Any]) -> Education:
        """
        Parse a single education entry from a JSON dict.

        Args:
            data: Education dictionary with keys like institution, degree, field.

        Returns:
            Education entity.
        """
        institution = str(data.get("institution", data.get("school", data.get("university", "")))).strip()
        degree = str(data.get("degree", "")).strip()
        field = str(data.get("field", data.get("major", data.get("field_of_study", "")))).strip()

        return Education(
            institution=institution,
            degree=degree,
            field=field,
        )
