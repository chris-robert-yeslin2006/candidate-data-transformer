"""
CSV parser unit tests.

Tests the CsvParser implementation including:
- Standard CSV parsing with default column mapping
- Custom column mapping overrides
- Missing optional fields
- Unknown column handling
- Malformed CSV handling
- Empty value handling
- Skills parsing with different delimiters
- Provenance metadata attachment
- Warning generation
- Bytes input handling
"""

from datetime import datetime

import pytest

from app.core.exceptions import ParsingError
from app.domain.models import CanonicalCandidate
from app.domain.models.provenance import SourceType
from app.parsers.csv_parser import CsvParser

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def parser() -> CsvParser:
    """Return a default CsvParser instance."""
    return CsvParser()


@pytest.fixture
def standard_csv() -> str:
    """
    Standard CSV with common candidate columns.
    """
    return (
        "name,email,phone,skills,title,company,summary\n"
        "John Doe,john@example.com,+1-555-0100,Python|FastAPI|Docker,"
        "Software Engineer,Acme Corp,A seasoned software engineer"
    )


@pytest.fixture
def minimal_csv() -> str:
    """CSV with only name and email."""
    return "name,email\nJane Smith,jane@example.com"


@pytest.fixture
def custom_mapping_csv() -> str:
    """CSV with non-standard column names."""
    return (
        "Full Name,Email Address,Mobile Number\n"
        "Alice Johnson,alice@example.com,+1-555-0200"
    )


@pytest.fixture
def skills_pipe_csv() -> str:
    """CSV with pipe-delimited skills."""
    return (
        "name,skills\n"
        "Bob,Python|Java|C++"
    )


@pytest.fixture
def skills_semicolon_csv() -> str:
    """CSV with semicolon-delimited skills."""
    return (
        "name,skills\n"
        "Carol,Python;JavaScript;TypeScript"
    )


@pytest.fixture
def skills_comma_csv() -> str:
    """CSV with comma-delimited skills (single string, not CSV)."""
    return (
        "name,skills\n"
        "Dave,Python,JavaScript,Go"
    )


@pytest.fixture
def emoji_name_csv() -> str:
    """CSV with non-ASCII characters in name field."""
    return "name,email,phone\nJosé García,jose@example.com,+34-600-000-000"


@pytest.fixture
def empty_values_csv() -> str:
    """CSV with some empty cell values."""
    return (
        "name,email,phone,skills,title\n"
        "Empty Fields Test,,+1-555-0300,,Engineer"
    )


@pytest.fixture
def only_unknown_columns_csv() -> str:
    """CSV where none of the columns match the default mapping."""
    return "Foo,Bar,Baz\na,b,c"


@pytest.fixture
def long_csv() -> str:
    """CSV with multiple rows (parser should only use first)."""
    return (
        "name,email\n"
        "First Row,first@example.com\n"
        "Second Row,second@example.com\n"
        "Third Row,third@example.com"
    )


@pytest.fixture
def first_name_csv() -> str:
    """CSV with first_name/last_name columns."""
    return (
        "first_name,last_name,email\n"
        "John,Doe,john.doe@example.com"
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestCsvParserHappyPath:
    """Tests for standard, expected CSV input."""

    def test_standard_csv(self, parser: CsvParser, standard_csv: str) -> None:
        """Parse a standard CSV with name, email, phone, skills."""
        result = parser.parse(standard_csv)

        assert isinstance(result, CanonicalCandidate)
        assert result.name.first == ""
        assert result.name.display_name == "John Doe"
        assert result.contact is not None
        assert len(result.contact.emails) == 1
        assert result.contact.emails[0].value == "john@example.com"
        assert result.contact.emails[0].is_primary is True
        assert len(result.contact.phones) == 1
        assert result.contact.phones[0].value == "+1-555-0100"
        assert len(result.skills) == 3
        assert result.skills[0].name == "Python"
        assert result.skills[1].name == "FastAPI"
        assert result.skills[2].name == "Docker"
        assert len(result.experience) == 1
        assert result.experience[0].title == "Software Engineer"
        assert result.summary == "A seasoned software engineer"

    def test_minimal_csv(self, parser: CsvParser, minimal_csv: str) -> None:
        """Parse a minimal CSV with only name and email."""
        result = parser.parse(minimal_csv)

        assert result.name.display_name == "Jane Smith"
        assert result.contact is not None
        assert result.contact.emails[0].value == "jane@example.com"
        assert result.contact.phones == []
        assert result.skills == []
        assert result.summary == ""

    def test_bytes_input(self, parser: CsvParser, standard_csv: str) -> None:
        """Parser should handle bytes input."""
        result = parser.parse(standard_csv.encode("utf-8"))
        assert result.name.display_name == "John Doe"

    def test_custom_column_mapping(
        self, standard_csv: str
    ) -> None:
        """Custom column mapping should override defaults."""
        parser = CsvParser(column_mapping={
            "name": "name.display_name",
            "email": "contact.emails[0].value",
            "phone": "contact.phones[0].value",
            "skills": "skills",
            "title": "experience[0].title",
            "company": "experience[0].organization.name",
            "summary": "summary",
        })
        result = parser.parse(standard_csv)
        assert result.name.display_name == "John Doe"
        assert result.contact is not None
        assert result.contact.emails[0].value == "john@example.com"

    def test_custom_mapping_via_kwargs(
        self, parser: CsvParser, custom_mapping_csv: str
    ) -> None:
        """Column mapping can be passed via parse() kwargs."""
        mapping = {
            "Full Name": "name.display_name",
            "Email Address": "contact.emails[0].value",
            "Mobile Number": "contact.phones[0].value",
        }
        result = parser.parse(custom_mapping_csv, column_mapping=mapping)
        assert result.name.display_name == "Alice Johnson"
        assert result.contact is not None
        assert result.contact.emails[0].value == "alice@example.com"
        assert result.contact.phones[0].value == "+1-555-0200"

    def test_skills_pipe_delimiter(
        self, parser: CsvParser, skills_pipe_csv: str
    ) -> None:
        """Skills with pipe delimiter should be split correctly."""
        result = parser.parse(skills_pipe_csv)
        assert [s.name for s in result.skills] == ["Python", "Java", "C++"]

    def test_skills_semicolon_delimiter(
        self, parser: CsvParser, skills_semicolon_csv: str
    ) -> None:
        """Skills with semicolon delimiter should be split correctly."""
        result = parser.parse(skills_semicolon_csv)
        assert [s.name for s in result.skills] == ["Python", "JavaScript", "TypeScript"]

    def test_emoji_name(self, parser: CsvParser, emoji_name_csv: str) -> None:
        """Non-ASCII characters in name should be preserved."""
        result = parser.parse(emoji_name_csv)
        assert result.name.display_name == "José García"
        assert result.contact is not None
        assert result.contact.emails[0].value == "jose@example.com"

    def test_first_name_last_name(
        self, parser: CsvParser, first_name_csv: str
    ) -> None:
        """CSV with first_name/last_name should populate PersonName."""
        result = parser.parse(first_name_csv)
        assert result.name.first == "John"
        assert result.name.last == "Doe"
        assert result.name.display_name == ""
        assert result.contact is not None
        assert result.contact.emails[0].value == "john.doe@example.com"

    def test_long_csv_uses_first_row_only(
        self, parser: CsvParser, long_csv: str
    ) -> None:
        """Only the first data row should be parsed."""
        result = parser.parse(long_csv)
        assert result.name.display_name == "First Row"
        assert result.contact is not None
        assert result.contact.emails[0].value == "first@example.com"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestCsvParserEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_values(
        self, parser: CsvParser, empty_values_csv: str
    ) -> None:
        """Empty cell values should result in default/empty fields."""
        result = parser.parse(empty_values_csv)
        assert result.name.display_name == "Empty Fields Test"
        assert result.contact is not None
        assert result.contact.emails == []
        assert result.contact.phones[0].value == "+1-555-0300"
        assert result.skills == []

    def test_only_unknown_columns(
        self, parser: CsvParser, only_unknown_columns_csv: str
    ) -> None:
        """CSV with no matching columns should produce empty candidate."""
        result = parser.parse(only_unknown_columns_csv)
        assert result.name.display_name == ""
        assert result.contact is None
        assert result.skills == []

    def test_empty_csv(self, parser: CsvParser) -> None:
        """Empty CSV string should raise ParsingError."""
        with pytest.raises(ParsingError, match="CSV has no header row"):
            parser.parse("")

    def test_header_only_csv(self, parser: CsvParser) -> None:
        """CSV with headers but no data rows should raise ParsingError."""
        with pytest.raises(ParsingError, match="is empty"):
            parser.parse("name,email,phone")

    def test_malformed_csv(self, parser: CsvParser) -> None:
        """Garbled CSV should raise ParsingError."""
        with pytest.raises(ParsingError):
            parser.parse("\x00\x00\x00\x00")

    def test_single_column_csv(self, parser: CsvParser) -> None:
        """CSV with a single column that doesn't match any mapping."""
        result = parser.parse("notes\nHello world")
        assert result.name.display_name == ""
        assert result.contact is None

    def test_extra_whitespace_in_headers(self, parser: CsvParser) -> None:
        """Column headers with extra whitespace should still match."""
        csv_data = " name , email , phone \nJohn,john@example.com,+1-555-0100"
        result = parser.parse(csv_data)
        assert result.name.display_name == "John"

    def test_csv_with_bom(self, parser: CsvParser) -> None:
        """CSV with BOM should be handled (stripped by DictReader)."""
        csv_data = "\ufeffname,email\nTest,test@example.com"
        result = parser.parse(csv_data)
        assert result.name.display_name == "Test"
        assert result.contact is not None
        assert result.contact.emails[0].value == "test@example.com"

    def test_newlines_in_values(self, parser: CsvParser) -> None:
        """CSV values with embedded newlines should be handled."""
        csv_data = 'name,description\nMulti Line,"Line 1\nLine 2\nLine 3"'
        result = parser.parse(csv_data)
        assert result.name.display_name == "Multi Line"

    def test_null_bytes(self, parser: CsvParser) -> None:
        """CSV with null bytes should not raise (graceful handling)."""
        result = parser.parse("name,email\n\x00,\x00")
        assert isinstance(result, CanonicalCandidate)


# ---------------------------------------------------------------------------
# Skills parsing
# ---------------------------------------------------------------------------


class TestSkillsParsing:
    """Tests for skill list parsing with various delimiters."""

    def test_single_skill(self, parser: CsvParser) -> None:
        """Single skill with no delimiter should be a single-element list."""
        csv_data = "name,skills\nUser,Python"
        result = parser.parse(csv_data)
        assert [s.name for s in result.skills] == ["Python"]

    def test_pipe_skills(self, parser: CsvParser) -> None:
        """Skills separated by pipe."""
        csv_data = "name,skills\nUser,A|B|C"
        result = parser.parse(csv_data)
        assert [s.name for s in result.skills] == ["A", "B", "C"]

    def test_semicolon_skills(self, parser: CsvParser) -> None:
        """Skills separated by semicolon."""
        csv_data = "name,skills\nUser,X;Y;Z"
        result = parser.parse(csv_data)
        assert [s.name for s in result.skills] == ["X", "Y", "Z"]

    def test_empty_skill_entries_stripped(self, parser: CsvParser) -> None:
        """Empty skill entries should be stripped from the list."""
        csv_data = "name,skills\nUser,Python;;Java;"
        result = parser.parse(csv_data)
        assert [s.name for s in result.skills] == ["Python", "Java"]


# ---------------------------------------------------------------------------
# Warnings and provenance
# ---------------------------------------------------------------------------


class TestParserWarnings:
    """Tests for warning generation and provenance metadata."""

    def test_unknown_column_warning(self, parser: CsvParser) -> None:
        """Unknown columns should generate warnings."""
        csv_data = "name,email,UNKNOWN_COL\nTest,test@example.com,value"
        result = parser.parse(csv_data)
        assert result.metadata is not None
        unknown_warnings = [
            w for w in result.metadata.warnings
            if w.code == "UNKNOWN_COLUMN"
        ]
        assert len(unknown_warnings) >= 1
        assert "UNKNOWN_COL" in unknown_warnings[0].message

    def test_missing_column_warning(self, parser: CsvParser) -> None:
        """Expected but absent columns should generate warnings."""
        csv_data = "name\nOnly Name"
        result = parser.parse(csv_data)
        assert result.metadata is not None
        missing_warnings = [
            w for w in result.metadata.warnings
            if w.code == "MISSING_COLUMN"
        ]
        assert len(missing_warnings) >= 1

    def test_provenance_metadata_attached(self, parser: CsvParser) -> None:
        """Parse result should have ProcessingMetadata with provenance info."""
        csv_data = "name,email\nTest,test@example.com"
        result = parser.parse(csv_data, source_id="test_file.csv")
        assert result.metadata is not None
        assert SourceType.CSV in result.metadata.source_types
        assert result.metadata.parser_version == "1.0.0"
        assert isinstance(result.metadata.created_at, datetime)
        assert isinstance(result.metadata.updated_at, datetime)

    def test_no_unknown_column_warnings_for_standard_csv(
        self, parser: CsvParser, standard_csv: str
    ) -> None:
        """Standard CSV columns should all be recognized (no UNKNOWN_COLUMN warnings)."""
        result = parser.parse(standard_csv)
        assert result.metadata is not None
        unknown_warnings = [
            w for w in result.metadata.warnings
            if w.code == "UNKNOWN_COLUMN"
        ]
        assert len(unknown_warnings) == 0


# ---------------------------------------------------------------------------
# Column mapping
# ---------------------------------------------------------------------------


class TestColumnMapping:
    """Tests for configurable column mapping behavior."""

    def test_empty_mapping(self) -> None:
        """Parser with empty mapping should produce empty candidate."""
        parser = CsvParser(column_mapping={})
        result = parser.parse("name,email\nTest,test@example.com")
        assert result.name.display_name == ""
        assert result.contact is None

    def test_partial_mapping(self) -> None:
        """Parser with partial mapping should map only specified columns."""
        parser = CsvParser(column_mapping={
            "name": "name.display_name",
        })
        result = parser.parse("name,email,phone\nTest,test@example.com,123")
        assert result.name.display_name == "Test"
        assert result.contact is None

    def test_warning_codes_match(self, parser: CsvParser) -> None:
        """Warning codes should be consistent and descriptive."""
        csv_data = "name,email\nTest,test@example.com"
        result = parser.parse(csv_data)
        assert result.metadata is not None
        for w in result.metadata.warnings:
            assert w.code in ("MISSING_COLUMN", "UNKNOWN_COLUMN")
            assert w.source == "csv_parser"
            assert isinstance(w.message, str)
            assert len(w.message) > 0
