"""
CSVReader — reads CSV content and produces CSVRecord objects.

Responsible for:
    - Decoding bytes to str (UTF-8)
    - Stripping UTF-8 BOM
    - Parsing CSV rows with configurable delimiter
    - Producing CSVRecord objects (one per data row)

Has zero knowledge of candidates, field mappings, or domains.
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Any

from app.core.exceptions import ParsingError
from app.parsers.csv_record import CSVRecord

logger = logging.getLogger(__name__)


class CSVReader:
    """
    Low-level CSV file reader.

    Reads CSV content and produces a list of CSVRecord objects.
    The delimiter can be configured, making this reusable for
    TSV and other delimited formats.

    Args:
        delimiter: Single-character field delimiter (default: ',').
    """

    def __init__(self, delimiter: str = ",") -> None:
        self._delimiter = delimiter

    def read(self, raw_data: str | bytes, **kwargs: Any) -> list[CSVRecord]:
        """
        Parse CSV content into a list of CSVRecord objects.

        Args:
            raw_data: CSV content as string or UTF-8 bytes.
            **kwargs: Unused — reserved for future reader options.

        Returns:
            List of CSVRecord, one per data row.

        Raises:
            ParsingError: If the CSV is malformed or has no headers.
        """
        raw_str = self._normalize_input(raw_data)

        reader, headers = self._parse_headers(raw_str)

        records: list[CSVRecord] = []
        for row_number, row in enumerate(reader, start=1):
            values = tuple(row.get(h, "") for h in headers)
            records.append(
                CSVRecord(
                    row_number=row_number,
                    headers=headers,
                    values=values,
                )
            )

        return records

    def _normalize_input(self, raw_data: str | bytes) -> str:
        """
        Convert bytes to string and strip UTF-8 BOM.

        Args:
            raw_data: Input as string or bytes.

        Returns:
            Normalised UTF-8 string without BOM prefix.
        """
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode("utf-8")
        return raw_data.lstrip("\ufeff")

    def _parse_headers(self, raw_str: str) -> tuple[csv.DictReader[str], tuple[str, ...]]:
        """
        Parse the CSV header row.

        Args:
            raw_str: BOM-stripped CSV string.

        Returns:
            Tuple of (DictReader, tuple of header strings).

        Raises:
            ParsingError: If headers are missing or CSV is malformed.
        """
        try:
            reader = csv.DictReader(
                io.StringIO(raw_str), delimiter=self._delimiter,
            )
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

        return reader, tuple(headers)
