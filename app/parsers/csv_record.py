"""
CSVRecord — an immutable representation of a single CSV row.

Sits as the seam between Reader and Mapper. Readers produce
CSVRecord objects; the CandidateMapper consumes them. This
type has zero knowledge of candidates, parsers, or domains.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CSVRecord:
    """
    Immutable representation of one CSV data row.

    Attributes:
        row_number: 1-based index of this row within the file.
        headers: Ordered tuple of column header strings.
        values: Ordered tuple of cell values, same length as headers.
    """

    row_number: int
    headers: tuple[str, ...]
    values: tuple[str, ...]

    def get(self, header: str) -> str:
        """
        Return the cell value for a given header.

        Args:
            header: Header name to look up (exact match).

        Returns:
            Cell value, or empty string if not found.
        """
        for h, v in zip(self.headers, self.values):
            if h == header:
                return v
        return ""
