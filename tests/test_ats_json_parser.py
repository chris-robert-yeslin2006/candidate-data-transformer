"""Tests for AtsJsonParser."""

import json

import pytest

from app.parsers.ats_json_parser import AtsJsonParser


class TestAtsJsonParser:
    """Tests for ATS JSON parser."""

    def setup_method(self) -> None:
        self.parser = AtsJsonParser()

    def test_parse_complete_candidate(self) -> None:
        """Parse a fully populated JSON candidate."""
        data = json.dumps({
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "skills": ["Python", "JavaScript"],
            "title": "Senior Engineer",
            "company": "Acme Corp",
            "summary": "Experienced engineer",
        })

        result = self.parser.parse(data)

        assert result.name.display_name == "John Doe"
        assert result.contact is not None
        assert result.contact.emails[0].value == "john@example.com"
        assert result.contact.phones[0].value == "+1234567890"
        assert len(result.skills) == 2
        assert result.skills[0].name == "Python"
        assert result.summary == "Experienced engineer"
        assert len(result.experience) == 1
        assert result.experience[0].title == "Senior Engineer"

    def test_parse_first_last_name(self) -> None:
        """Parse JSON with separate first/last name fields."""
        data = json.dumps({
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
        })

        result = self.parser.parse(data)

        assert result.name.first == "Jane"
        assert result.name.last == "Smith"
        assert result.name.display_name == "Jane Smith"

    def test_parse_with_experience_list(self) -> None:
        """Parse JSON with a list of work experience entries."""
        data = json.dumps({
            "name": "John Doe",
            "work_experience": [
                {"title": "Senior Engineer", "company": "Acme"},
                {"title": "Junior Engineer", "company": "StartupXYZ"},
            ],
        })

        result = self.parser.parse(data)

        assert len(result.experience) == 2
        assert result.experience[0].title == "Senior Engineer"
        assert result.experience[1].title == "Junior Engineer"

    def test_parse_with_education_list(self) -> None:
        """Parse JSON with education entries."""
        data = json.dumps({
            "name": "John Doe",
            "education": [
                {
                    "institution": "MIT",
                    "degree": "B.S.",
                    "field": "Computer Science",
                }
            ],
        })

        result = self.parser.parse(data)

        assert len(result.education) == 1
        assert result.education[0].institution == "MIT"
        assert result.education[0].degree == "B.S."

    def test_parse_skills_as_comma_string(self) -> None:
        """Parse skills provided as a comma-separated string."""
        data = json.dumps({
            "name": "John",
            "skills": "Python, JavaScript, SQL",
        })

        result = self.parser.parse(data)

        assert len(result.skills) == 3
        assert result.skills[0].name == "Python"

    def test_parse_skills_as_dict_list(self) -> None:
        """Parse skills provided as list of dicts."""
        data = json.dumps({
            "name": "John",
            "skills": [{"name": "Python"}, {"name": "Java"}],
        })

        result = self.parser.parse(data)

        assert len(result.skills) == 2
        assert result.skills[0].name == "Python"

    def test_parse_empty_json_raises(self) -> None:
        """Empty string raises ParsingError."""
        with pytest.raises(Exception):
            self.parser.parse("")

    def test_parse_malformed_json_raises(self) -> None:
        """Malformed JSON raises ParsingError."""
        with pytest.raises(Exception):
            self.parser.parse("{invalid json")

    def test_parse_non_dict_raises(self) -> None:
        """JSON array raises ParsingError."""
        with pytest.raises(Exception):
            self.parser.parse("[1, 2, 3]")

    def test_parse_missing_optional_fields(self) -> None:
        """Missing optional fields default to empty."""
        data = json.dumps({"name": "John Doe"})
        result = self.parser.parse(data)

        assert result.name.display_name == "John Doe"
        assert result.skills == []
        assert result.experience == []
        assert result.education == []
        assert result.summary == ""

    def test_unknown_keys_generate_warnings(self) -> None:
        """Unknown JSON keys produce warnings in metadata."""
        data = json.dumps({
            "name": "John",
            "unknown_field": "value",
            "another_unknown": 42,
        })

        result = self.parser.parse(data)

        assert result.metadata is not None
        unknown_warnings = [
            w for w in result.metadata.warnings if w.code == "UNKNOWN_KEY"
        ]
        assert len(unknown_warnings) >= 1

    def test_parse_bytes_input(self) -> None:
        """Parser handles bytes input."""
        data = json.dumps({"name": "John"}).encode("utf-8")
        result = self.parser.parse(data)

        assert result.name.display_name == "John"

    def test_metadata_attached(self) -> None:
        """Parser attaches ProcessingMetadata."""
        data = json.dumps({"name": "John"})
        result = self.parser.parse(data)

        assert result.metadata is not None
        assert result.metadata.parser_version == "1.0.0"
        assert "ats_json" in result.metadata.source_types
