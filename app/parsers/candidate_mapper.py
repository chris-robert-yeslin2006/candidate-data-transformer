"""
CandidateMapper — maps a CSVRecord into a CanonicalCandidate.

Responsible for:
    - Configurable column name mapping (CSV column → field path)
    - Case-insensitive header matching
    - Missing / unknown column warnings
    - List-field parsing (skills with | ; , delimiters)
    - Experience field accumulation
    - Nested field assignment on the candidate model

Has zero knowledge of file formats, delimiters, or encoding.
"""

from __future__ import annotations

import logging

from app.domain.models import (
    CanonicalCandidate,
    ContactInformation,
    Email,
    Experience,
    Phone,
    Skill,
)
from app.domain.models.warning import Warning as ProcessingWarning
from app.parsers.csv_record import CSVRecord

logger = logging.getLogger(__name__)

# Default mapping from CSV column names to CanonicalCandidate field paths.
# Keys are case-insensitive during matching.
DEFAULT_COLUMN_MAPPING: dict[str, str] = {
    "name": "name.display_name",
    "first_name": "name.first",
    "last_name": "name.last",
    "middle_name": "name.middle",
    "email": "contact.emails[0].value",
    "phone": "contact.phones[0].value",
    "phone_number": "contact.phones[0].value",
    "mobile": "contact.phones[0].value",
    "skills": "skills",
    "title": "experience[0].title",
    "company": "experience[0].organization.name",
    "experience": "experience[0].description",
    "summary": "summary",
}

# Field paths that represent list-type fields (expect comma-separated values)
LIST_FIELDS = {"skills"}

# Delimiters to try when parsing skill values, in priority order.
SKILLS_DELIMITERS = ["|", ";", ","]


class CandidateMapper:
    """
    Maps a single CSVRecord into a CanonicalCandidate.

    The mapper owns all column-mapping logic: matching column names
    to field paths (case-insensitive), converting string values to
    the correct model fields, generating warnings for missing or
    unknown columns, and assembling nested structures (skills,
    experience, contact).

    Args:
        column_mapping: Dict mapping CSV column names to canonical
                        field paths. Uses DEFAULT_COLUMN_MAPPING if None.
    """

    def __init__(
        self,
        column_mapping: dict[str, str] | None = None,
    ) -> None:
        self._column_mapping = DEFAULT_COLUMN_MAPPING if column_mapping is None else column_mapping
        logger.debug(
            "CandidateMapper initialized with %d column mappings",
            len(self._column_mapping),
        )

    def map(
        self,
        record: CSVRecord,
        column_mapping: dict[str, str] | None = None,
        source_id: str = "",
    ) -> tuple[CanonicalCandidate, list[ProcessingWarning]]:
        """
        Map a CSVRecord to a CanonicalCandidate.

        Args:
            record: CSVRecord to map.
            column_mapping: Optional per-call mapping override.
            source_id: Source identifier for provenance.

        Returns:
            Tuple of (CanonicalCandidate, list of ProcessingWarning).
        """
        mapping = self._column_mapping if column_mapping is None else column_mapping
        warnings: list[ProcessingWarning] = []

        header_map = self._build_header_map(record.headers, mapping, warnings)
        candidate = self._record_to_candidate(record, header_map, source_id, warnings)

        return candidate, warnings

    def _build_header_map(
        self,
        headers: tuple[str, ...],
        column_mapping: dict[str, str],
        warnings: list[ProcessingWarning],
    ) -> dict[str, str]:
        """
        Build a case-insensitive mapping from CSV headers to field paths.

        Unknown columns generate warnings but are ignored.
        Missing mapped columns generate warnings.

        Args:
            headers: CSV column header strings.
            column_mapping: Dict mapping column names to field paths.
            warnings: Accumulator list for processing warnings.

        Returns:
            Dict mapping matched CSV headers to canonical field paths.
        """
        header_map: dict[str, str] = {}
        header_lookup: dict[str, str] = {}

        for h in headers:
            key = h.strip().lower()
            if key not in header_lookup:
                header_lookup[key] = h

        for col_name, field_path in column_mapping.items():
            key = col_name.lower().strip()
            matched_header = header_lookup.get(key)
            if matched_header is not None:
                header_map[matched_header] = field_path
                logger.debug("Mapped column '%s' -> '%s'", matched_header, field_path)
            else:
                warnings.append(
                    ProcessingWarning(
                        message=f"Expected column '{col_name}' not found in CSV headers",
                        source="csv_parser",
                        code="MISSING_COLUMN",
                        field=field_path,
                    )
                )

        # Warn about columns that were not matched by any mapping entry
        matched_keys = {h.strip().lower() for h in header_map}
        for h in headers:
            if h.strip().lower() not in matched_keys:
                warnings.append(
                    ProcessingWarning(
                        message=f"Ignoring unknown column '{h}'",
                        source="csv_parser",
                        code="UNKNOWN_COLUMN",
                        field="",
                    )
                )

        return header_map

    def _record_to_candidate(
        self,
        record: CSVRecord,
        header_map: dict[str, str],
        source_id: str,
        warnings: list[ProcessingWarning],
    ) -> CanonicalCandidate:
        """
        Convert a CSVRecord into a populated CanonicalCandidate.

        Args:
            record: The CSV data row.
            header_map: Mapping from CSV headers to field paths.
            source_id: Source identifier.
            warnings: Accumulator list for processing warnings.

        Returns:
            Populated CanonicalCandidate.
        """
        candidate = CanonicalCandidate()
        contact = ContactInformation()
        raw_skills: list[str] = []
        raw_experiences: list[dict[str, str]] = []

        for header, field_path in header_map.items():
            value = record.get(header).strip()

            if not value:
                continue

            if field_path in LIST_FIELDS:
                raw_skills = self._parse_skill_list(value, warnings, header)
                continue

            if field_path.startswith("experience"):
                self._accumulate_experience(
                    raw_experiences, field_path, value, warnings, header,
                )
                continue

            self._set_nested_field(
                candidate, contact, field_path, value, warnings, header,
            )

        contact.emails = [e for e in contact.emails if e.value]
        contact.phones = [p for p in contact.phones if p.value]
        candidate.contact = contact if (contact.emails or contact.phones) else None

        candidate.skills = [
            Skill(name=s.strip()) for s in raw_skills if s.strip()
        ]

        candidate.experience = [
            Experience(
                title=exp.get("title", ""),
                organization=None,
                description=exp.get("description", ""),
            )
            for exp in raw_experiences
        ]

        return candidate

    def _parse_skill_list(
        self,
        value: str,
        warnings: list[ProcessingWarning],
        header: str,
    ) -> list[str]:
        """
        Parse a skill list string that may use |, ;, or , as delimiter.

        Args:
            value: Raw skill string.
            warnings: Accumulator list.
            header: CSV column name for warning context.

        Returns:
            List of individual skill name strings.
        """
        for delim in SKILLS_DELIMITERS:
            if delim in value:
                return [s.strip() for s in value.split(delim) if s.strip()]
        return [value.strip()]

    def _accumulate_experience(
        self,
        experiences: list[dict[str, str]],
        field_path: str,
        value: str,
        warnings: list[ProcessingWarning],
        header: str,
    ) -> None:
        """
        Accumulate experience fields into a list of dicts.

        Supports paths like:
            experience[0].title
            experience[0].organization.name
            experience[0].description

        Args:
            experiences: Mutable list of experience dicts.
            field_path: Dot-path like "experience[0].title".
            value: The cell value.
            warnings: Accumulator list.
            header: CSV column name.
        """
        if not experiences:
            experiences.append({})

        _, _, subfield = field_path.partition(".")
        experiences[0][subfield] = value

    def _set_nested_field(
        self,
        candidate: CanonicalCandidate,
        contact: ContactInformation,
        field_path: str,
        value: str,
        warnings: list[ProcessingWarning],
        header: str,
    ) -> None:
        """
        Set a value on the candidate or contact model by dot-path.

        Supports paths like:
            name.display_name
            name.first
            contact.emails[0].value
            contact.phones[0].value
            summary

        Args:
            candidate: Target CanonicalCandidate.
            contact: Target ContactInformation accumulator.
            field_path: Dot-path to set.
            value: The value to set.
            warnings: Warning accumulator.
            header: CSV column name.
        """
        if field_path == "summary":
            candidate.summary = value
            return

        if field_path == "name.display_name" and not candidate.name.display_name:
            candidate.name.display_name = value
            return

        if field_path == "name.first":
            candidate.name.first = value
            return

        if field_path == "name.last":
            candidate.name.last = value
            return

        if field_path == "name.middle":
            candidate.name.middle = value
            return

        if field_path == "contact.emails[0].value":
            if not contact.emails:
                contact.emails.append(Email(value=value, type="", is_primary=True))
            else:
                contact.emails[0].value = value
            return

        if field_path == "contact.phones[0].value":
            if not contact.phones:
                contact.phones.append(Phone(value=value, type="", is_primary=True))
            else:
                contact.phones[0].value = value
            return
