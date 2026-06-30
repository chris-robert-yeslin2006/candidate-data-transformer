"""
CSV source parser — coordinates CSVReader → CandidateMapper.

Now a thin orchestrator: delegates file reading to CSVReader and
field mapping to CandidateMapper. No longer contains low-level
CSV parsing or mapping logic.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.core.exceptions import ParsingError
from app.domain.models import CanonicalCandidate
from app.domain.models.metadata import ProcessingMetadata
from app.domain.models.provenance import SourceType
from app.parsers.base import BaseParser
from app.parsers.candidate_mapper import (
    DEFAULT_COLUMN_MAPPING,
    CandidateMapper,
)
from app.parsers.csv_reader import CSVReader

logger = logging.getLogger(__name__)

DEFAULT_COLUMN_MAPPING = DEFAULT_COLUMN_MAPPING


class CsvParser(BaseParser):
    """
    Parser for CSV-encoded candidate data.

    Coordinates CSVReader (file reading) and CandidateMapper
    (field mapping) to convert CSV content into a validated
    CanonicalCandidate.

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
        self._column_mapping = DEFAULT_COLUMN_MAPPING if column_mapping is None else column_mapping
        self._reader = CSVReader()
        self._mapper = CandidateMapper()
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

        records = self._reader.read(raw_data)
        if not records:
            raise ParsingError("CSV file is empty")

        candidate, warnings = self._mapper.map(
            records[0],
            column_mapping=column_mapping,
            source_id=source_id,
        )

        candidate.metadata = ProcessingMetadata(
            created_at=datetime.now(),
            updated_at=datetime.now(),
            parser_version=self.parser_version,
            source_types=[SourceType.CSV],
            warnings=warnings,
        )

        return candidate
