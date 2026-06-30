"""
CSVReader unit tests.

Tests the CSVReader in isolation — no candidate or domain knowledge.
"""

import pytest

from app.core.exceptions import ParsingError
from app.parsers.csv_reader import CSVReader


class TestCSVReader:
    """Tests for the low-level CSV file reader."""

    def test_basic_csv(self) -> None:
        """Basic CSV should produce one record with correct data."""
        reader = CSVReader()
        records = reader.read("name,email\nJohn,john@example.com")

        assert len(records) == 1
        record = records[0]
        assert record.row_number == 1
        assert record.headers == ("name", "email")
        assert record.values == ("John", "john@example.com")

    def test_multiple_rows(self) -> None:
        """Multi-row CSV should produce a record per data row."""
        reader = CSVReader()
        records = reader.read("name,email\nA,a@c\nB,b@c")

        assert len(records) == 2
        assert records[0].row_number == 1
        assert records[0].get("name") == "A"
        assert records[1].row_number == 2
        assert records[1].get("name") == "B"

    def test_bytes_input(self) -> None:
        """Bytes input should be decoded as UTF-8."""
        reader = CSVReader()
        records = reader.read("x,y\n1,2".encode("utf-8"))
        assert len(records) == 1
        assert records[0].get("x") == "1"

    def test_strips_bom(self) -> None:
        """UTF-8 BOM should be stripped before parsing."""
        reader = CSVReader()
        records = reader.read("\ufeffa,b\nc,d")
        assert len(records) == 1
        assert records[0].get("a") == "c"

    def test_custom_delimiter(self) -> None:
        """Custom delimiter should work (for TSV reuse)."""
        reader = CSVReader(delimiter="\t")
        records = reader.read("name\temail\nJohn\tjohn@c.com")
        assert len(records) == 1
        assert records[0].get("name") == "John"
        assert records[0].get("email") == "john@c.com"

    def test_empty_csv_raises_error(self) -> None:
        """Empty string should raise ParsingError (no headers)."""
        reader = CSVReader()
        with pytest.raises(ParsingError, match="no header row"):
            reader.read("")

    def test_header_only_returns_empty_list(self) -> None:
        """CSV with headers but no data rows returns empty list."""
        reader = CSVReader()
        records = reader.read("name,email,phone")
        assert records == []

    def test_single_column_csv(self) -> None:
        """CSV with a single column should work."""
        reader = CSVReader()
        records = reader.read("notes\nHello world")
        assert len(records) == 1
        assert records[0].get("notes") == "Hello world"

    def test_record_immutability(self) -> None:
        """CSVRecord should be frozen (immutable)."""
        reader = CSVReader()
        records = reader.read("a,b\n1,2")
        record = records[0]
        with pytest.raises(AttributeError):
            record.headers = ("x",)  # type: ignore[misc]

    def test_csv_record_fields_match(self) -> None:
        """Headers and values tuples should be parallel and same length."""
        reader = CSVReader()
        records = reader.read("a,b,c\n1,2,3")
        assert len(records[0].headers) == 3
        assert len(records[0].values) == 3
        assert len(records[0].headers) == len(records[0].values)

    def test_empty_bytes_raises_error(self) -> None:
        """Empty bytes input should raise ParsingError (no headers)."""
        reader = CSVReader()
        with pytest.raises(ParsingError, match="no header row"):
            reader.read(b"")
