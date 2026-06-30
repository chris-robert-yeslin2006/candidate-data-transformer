"""
CandidateMapper unit tests.

Tests the CandidateMapper in isolation — no file I/O or CSV parsing.
Uses CSVRecord objects constructed directly in tests.
"""



from app.parsers.candidate_mapper import (
    CandidateMapper,
)
from app.parsers.csv_record import CSVRecord


def _record(
    row_number: int = 1,
    **fields: str,
) -> CSVRecord:
    """Build a CSVRecord from keyword arguments for concise test setup."""
    return CSVRecord(
        row_number=row_number,
        headers=tuple(fields.keys()),
        values=tuple(fields.values()),
    )


class TestCandidateMapperHappyPath:
    """Tests for standard, expected mapping."""

    def test_standard_record(self) -> None:
        """Standard columns should map to correct candidate fields."""
        mapping = {
            "name": "name.display_name",
            "email": "contact.emails[0].value",
            "phone": "contact.phones[0].value",
            "skills": "skills",
            "title": "experience[0].title",
            "company": "experience[0].organization.name",
            "summary": "summary",
        }
        mapper = CandidateMapper(column_mapping=mapping)
        record = _record(
            name="John Doe",
            email="john@example.com",
            phone="+1-555-0100",
            skills="Python|FastAPI|Docker",
            title="Software Engineer",
            company="Acme Corp",
            summary="A seasoned software engineer",
        )
        candidate, warnings = mapper.map(record)

        assert candidate.name.display_name == "John Doe"
        assert candidate.contact is not None
        assert candidate.contact.emails[0].value == "john@example.com"
        assert candidate.contact.phones[0].value == "+1-555-0100"
        assert [s.name for s in candidate.skills] == ["Python", "FastAPI", "Docker"]
        assert len(candidate.experience) == 1
        assert candidate.experience[0].title == "Software Engineer"
        assert candidate.summary == "A seasoned software engineer"
        assert len(warnings) == 0

    def test_minimal_record(self) -> None:
        """Only name and email should still produce valid candidate."""
        mapping = {
            "name": "name.display_name",
            "email": "contact.emails[0].value",
        }
        mapper = CandidateMapper(column_mapping=mapping)
        record = _record(name="Jane Smith", email="jane@example.com")
        candidate, warnings = mapper.map(record)

        assert candidate.name.display_name == "Jane Smith"
        assert candidate.contact is not None
        assert candidate.contact.emails[0].value == "jane@example.com"
        assert candidate.contact.phones == []
        assert candidate.skills == []
        assert candidate.summary == ""
        assert len(warnings) == 0

    def test_bytes_input(self) -> None:
        """Mapper operates on CSVRecord — bytes are a reader concern."""
        mapper = CandidateMapper()
        record = _record(name="Alice", email="alice@example.com")
        candidate, _ = mapper.map(record)
        assert candidate.name.display_name == "Alice"

    def test_custom_column_mapping(self) -> None:
        """Custom column mapping should override defaults."""
        mapper = CandidateMapper(column_mapping={
            "Full Name": "name.display_name",
            "Email Address": "contact.emails[0].value",
            "Mobile Number": "contact.phones[0].value",
        })
        record = CSVRecord(
            row_number=1,
            headers=("Full Name", "Email Address", "Mobile Number"),
            values=("Alice Johnson", "alice@example.com", "+1-555-0200"),
        )
        candidate, warnings = mapper.map(record)

        assert candidate.name.display_name == "Alice Johnson"
        assert candidate.contact is not None
        assert candidate.contact.emails[0].value == "alice@example.com"
        assert candidate.contact.phones[0].value == "+1-555-0200"
        assert len(warnings) == 0

    def test_per_call_mapping_override(self) -> None:
        """Mapping can be overridden per map() call."""
        mapper = CandidateMapper()
        record = CSVRecord(
            row_number=1,
            headers=("Full Name", "Email Address"),
            values=("Bob", "bob@example.com"),
        )
        mapping = {
            "Full Name": "name.display_name",
            "Email Address": "contact.emails[0].value",
        }
        candidate, warnings = mapper.map(record, column_mapping=mapping)

        assert candidate.name.display_name == "Bob"
        assert candidate.contact is not None
        assert candidate.contact.emails[0].value == "bob@example.com"
        assert len(warnings) == 0

    def test_skills_pipe(self) -> None:
        """Pipe-delimited skills should be split."""
        mapper = CandidateMapper()
        record = _record(name="Bob", skills="Python|Java|C++")
        candidate, _ = mapper.map(record)
        assert [s.name for s in candidate.skills] == ["Python", "Java", "C++"]

    def test_skills_semicolon(self) -> None:
        """Semicolon-delimited skills should be split."""
        mapper = CandidateMapper()
        record = _record(name="Carol", skills="Python;JavaScript;TypeScript")
        candidate, _ = mapper.map(record)
        assert [s.name for s in candidate.skills] == ["Python", "JavaScript", "TypeScript"]

    def test_first_name_last_name(self) -> None:
        """first_name/last_name columns should populate PersonName."""
        mapper = CandidateMapper()
        record = _record(first_name="John", last_name="Doe", email="john@c.com")
        candidate, _ = mapper.map(record)
        assert candidate.name.first == "John"
        assert candidate.name.last == "Doe"
        assert candidate.name.display_name == ""

    def test_unicode_name(self) -> None:
        """Non-ASCII characters should be preserved."""
        mapper = CandidateMapper()
        record = _record(name="José García", email="jose@example.com")
        candidate, _ = mapper.map(record)
        assert candidate.name.display_name == "José García"


class TestCandidateMapperEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_values(self) -> None:
        """Empty cell values should result in default/empty fields."""
        mapper = CandidateMapper()
        record = _record(
            name="Empty Fields Test",
            email="",
            phone="+1-555-0300",
            skills="",
            title="Engineer",
        )
        candidate, _ = mapper.map(record)

        assert candidate.name.display_name == "Empty Fields Test"
        assert candidate.contact is not None
        assert candidate.contact.emails == []
        assert candidate.contact.phones[0].value == "+1-555-0300"
        assert candidate.skills == []

    def test_no_matching_columns(self) -> None:
        """Record with no matching mapping should produce empty candidate."""
        mapper = CandidateMapper()
        record = _record(Foo="a", Bar="b", Baz="c")
        candidate, warnings = mapper.map(record)

        assert candidate.name.display_name == ""
        assert candidate.contact is None
        assert candidate.skills == []
        assert len(warnings) >= 3  # 3 unknown columns

    def test_empty_mapping(self) -> None:
        """Mapper with empty mapping should produce empty candidate."""
        mapper = CandidateMapper(column_mapping={})
        record = _record(name="Test", email="test@c.com")
        candidate, warnings = mapper.map(record)

        assert candidate.name.display_name == ""
        assert candidate.contact is None
        assert len(warnings) >= 2  # 2 unknown columns

    def test_partial_mapping(self) -> None:
        """Mapper with partial mapping should map only those columns."""
        mapper = CandidateMapper(column_mapping={
            "name": "name.display_name",
        })
        record = _record(name="Test", email="test@c.com", phone="123")
        candidate, _ = mapper.map(record)

        assert candidate.name.display_name == "Test"
        assert candidate.contact is None

    def test_single_skill(self) -> None:
        """Single skill with no delimiter."""
        mapper = CandidateMapper()
        record = _record(name="User", skills="Python")
        candidate, _ = mapper.map(record)
        assert [s.name for s in candidate.skills] == ["Python"]

    def test_empty_skill_entries_stripped(self) -> None:
        """Empty entries in skill list should be removed."""
        mapper = CandidateMapper()
        record = _record(name="User", skills="Python;;Java;")
        candidate, _ = mapper.map(record)
        assert [s.name for s in candidate.skills] == ["Python", "Java"]


class TestMapperWarnings:
    """Tests for warning generation."""

    def test_unknown_column_warning(self) -> None:
        """Unknown columns should generate warnings."""
        mapper = CandidateMapper()
        record = _record(name="Test", email="t@t.com", UNKNOWN_COL="value")
        _, warnings = mapper.map(record)

        unknown = [w for w in warnings if w.code == "UNKNOWN_COLUMN"]
        assert len(unknown) >= 1
        assert "UNKNOWN_COL" in unknown[0].message

    def test_missing_column_warning(self) -> None:
        """Expected but absent columns should generate warnings."""
        mapper = CandidateMapper()
        record = _record(name="Only Name")
        _, warnings = mapper.map(record)

        missing = [w for w in warnings if w.code == "MISSING_COLUMN"]
        assert len(missing) >= 1

    def test_no_false_unknown_warnings_for_whitespace_headers(self) -> None:
        """Whitespace-padded headers that match should not produce unknown warnings."""
        mapper = CandidateMapper()
        record = CSVRecord(
            row_number=1,
            headers=(" name ", " email "),
            values=("John", "john@c.com"),
        )
        _, warnings = mapper.map(record)

        unknown = [w for w in warnings if w.code == "UNKNOWN_COLUMN"]
        warning_cols = {w.message.split("'")[1] for w in unknown if "'" in w.message}
        # " name " and " email " match our mapping, so they should NOT be in unknown warnings
        assert " name " not in warning_cols
        assert " email " not in warning_cols

    def test_warning_codes_match(self) -> None:
        """Warning codes should be consistent."""
        mapper = CandidateMapper()
        record = _record(name="Test", email="t@t.com")
        _, warnings = mapper.map(record)

        for w in warnings:
            assert w.code in ("MISSING_COLUMN", "UNKNOWN_COLUMN")
            assert w.source == "csv_parser"
            assert isinstance(w.message, str)
            assert len(w.message) > 0
