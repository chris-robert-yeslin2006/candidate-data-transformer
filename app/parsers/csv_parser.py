"""
CSV source parser.

Handles structured candidate data in CSV format. Maps column headers
to canonical field names using a configurable column mapping.

This is the first production parser and validates the parser framework
with deterministic structured input. It supports:

- Configurable column name mapping (CSV column -> CanonicalCandidate field)
- Automatic column detection for standard header names
- Unknown column ignoring
- Graceful handling of missing optional fields
- Structured warnings for data quality issues
- Baseline provenance metadata attachment
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime
from typing import Any

from app.core.exceptions import ParsingError
from app.domain.models import (
    CanonicalCandidate,
    ContactInformation,
    Email,
    Experience,
    Phone,
    Skill,
)
from app.domain.models.metadata import ProcessingMetadata
from app.domain.models.provenance import SourceType
from app.domain.models.warning import Warning as ProcessingWarning
from app.parsers.base import BaseParser

logger = logging.getLogger(__name__)

# Default mapping from CSV column names to CanonicalCandidate field paths.
# Used when no explicit mapping is provided. Keys are case-insensitive.
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

# Fields that should be split on a delimiter
SKILLS_DELIMITERS = ["|", ";", ","]


class CsvParser(BaseParser):
    """
    Parser for CSV-encoded candidate data.

    Reads CSV content using csv.DictReader, maps column headers to
    canonical model fields via a configurable mapping, ignores unknown
    columns, and returns a validated CanonicalCandidate.

    Handles:
        - Standard CSV with header row
        - Configurable column name mapping
        - Comma/pipe/semicolon-separated skill lists
        - Missing optional fields (defaults to empty)
        - Malformed CSV rows
        - Multiple candidate rows (only first row processed)

    Args:
        column_mapping: Optional override dict mapping CSV column names
                       to canonical field paths. Uses DEFAULT_COLUMN_MAPPING
                       if not provided.
    """

    source_type: SourceType = SourceType.CSV
    display_name: str = "CSV Parser"
    supported_extensions: list[str] = [".csv"]
    supported_mime_types: list[str] = ["text/csv"]
    requires_ai: bool = False
    parser_version: str = "1.0.0"

    def __init__(
        self,
        column_mapping: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize the CSV parser.

        Args:
            column_mapping: Custom CSV-to-candidate field mapping.
                            Falls back to DEFAULT_COLUMN_MAPPING if None.
        """
        self._column_mapping = DEFAULT_COLUMN_MAPPING if column_mapping is None else column_mapping
        logger.debug(
            "CsvParser initialized with %d column mappings",
            len(self._column_mapping),
        )

    def parse(
        self, raw_data: str | bytes, **kwargs: Any
    ) -> CanonicalCandidate:
        """
        Parse CSV content into a CanonicalCandidate.

        Args:
            raw_data: CSV content as a string.
            **kwargs:
                column_mapping: Optional per-call mapping override.
                source_id: Identifier for the source file/row.

        Returns:
            CanonicalCandidate with parsed fields.

        Raises:
            ParsingError: If the CSV data is malformed or empty.
        """
        column_mapping = kwargs.get("column_mapping", self._column_mapping)
        source_id = kwargs.get("source_id", "")

        # Normalize to string and strip BOM
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode("utf-8")
        raw_data = raw_data.lstrip("\ufeff")

        reader, headers = self._read_csv(raw_data)

        field_warnings: list[ProcessingWarning] = []

        # Build normalized lookup from CSV headers
        header_map = self._build_header_map(headers, column_mapping, field_warnings)

        # Process first data row only
        try:
            row = next(reader)
        except StopIteration:
            raise ParsingError("CSV file is empty")

        candidate = self._row_to_candidate(
            row, header_map, source_id, field_warnings
        )

        # Attach baseline provenance metadata
        candidate.metadata = ProcessingMetadata(
            created_at=datetime.now(),
            updated_at=datetime.now(),
            parser_version=self.parser_version,
            source_types=[SourceType.CSV],
            warnings=field_warnings,
        )

        return candidate

    def _read_csv(
        self, raw_data: str
    ) -> tuple[Any, list[str]]:
        """
        Parse the raw CSV string and return a DictReader and header list.

        Args:
            raw_data: CSV content as a string.

        Returns:
            Tuple of (csv.DictReader, list of header strings).

        Raises:
            ParsingError: If the CSV is malformed.
        """
        try:
            reader = csv.DictReader(io.StringIO(raw_data))
            headers = list(reader.fieldnames or [])
        except Exception as exc:
            raise ParsingError(
                f"Failed to parse CSV: {exc}",
                source_type="csv",
            )

        if not headers:
            raise ParsingError(
                "CSV has no header row",
                source_type="csv",
            )

        return reader, headers

    def _build_header_map(
        self,
        headers: list[str],
        column_mapping: dict[str, str],
        warnings: list[ProcessingWarning],
    ) -> dict[str, str]:
        """
        Build a case-insensitive mapping from CSV headers to field paths.

        Unknown columns generate warnings but are ignored.
        Missing mapped columns generate warnings.

        Args:
            headers: List of CSV column header strings.
            column_mapping: Dict mapping column names to field paths.
            warnings: Accumulator list for processing warnings.

        Returns:
            Dict mapping matched CSV headers to canonical field paths.
        """
        header_map: dict[str, str] = {}
        header_lookup = {h.strip().lower(): h for h in headers}

        for col_name, field_path in column_mapping.items():
            matched_header = header_lookup.get(col_name.lower().strip())
            if matched_header:
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

        # Warn about unmapped columns
        for h in headers:
            if h.strip() not in header_map:
                warnings.append(
                    ProcessingWarning(
                        message=f"Ignoring unknown column '{h}'",
                        source="csv_parser",
                        code="UNKNOWN_COLUMN",
                        field="",
                    )
                )

        return header_map

    def _row_to_candidate(
        self,
        row: dict[str, str],
        header_map: dict[str, str],
        source_id: str,
        warnings: list[ProcessingWarning],
    ) -> CanonicalCandidate:
        """
        Convert a single CSV row dict into a CanonicalCandidate.

        Args:
            row: Dict of CSV header -> cell value.
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
            value = row.get(header, "").strip()

            if not value:
                continue

            # Handle list-type fields
            if field_path in LIST_FIELDS:
                raw_skills = self._parse_skill_list(value, warnings, header)
                continue

            # Handle experience dictionary accumulation
            if field_path.startswith("experience"):
                self._accumulate_experience(
                    raw_experiences, field_path, value, warnings, header
                )
                continue

            # Set scalar values into the candidate model
            self._set_nested_field(
                candidate, contact, field_path, value, warnings, header
            )

        # Assemble contact information
        contact.emails = [e for e in contact.emails if e.value]
        contact.phones = [p for p in contact.phones if p.value]
        candidate.contact = contact if (contact.emails or contact.phones) else None

        # Assemble skills
        candidate.skills = [
            Skill(name=s.strip()) for s in raw_skills if s.strip()
        ]

        # Assemble experiences
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
            value: Raw skill string (e.g. "Python|FastAPI|Docker").
            warnings: Accumulator list for processing warnings.
            header: The CSV column name for warning context.

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
            header: The CSV column name.
        """
        if not experiences:
            experiences.append({})

        # Parse "experience[0].title" -> "experience[0]" path
        # and "title" subfield
        parts = field_path.split(".", 1)
        if len(parts) == 2:
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
            candidate: The target CanonicalCandidate.
            contact: The target ContactInformation accumulator.
            field_path: Dot-path to set (e.g. "name.display_name").
            value: The value to set.
            warnings: Warning accumulator.
            header: The CSV column name.
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
