"""Tests for TXT notes parser using MockGeminiClient."""

from app.clients.gemini import MockGeminiClient
from app.parsers.txt_parser import TxtNotesParser


class TestTxtNotesParser:
    """Tests for text notes parser with mock AI client."""

    def test_parse_with_fixture(self) -> None:
        """Parser maps mock response to candidate."""
        mock_client = MockGeminiClient(fixture={
            "name": "John Doe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "summary": "Strong candidate",
            "skills": ["Python", "SQL"],
            "experience": [
                {"title": "Engineer", "company": "Acme", "description": "Built things"}
            ],
            "education": [
                {"institution": "MIT", "degree": "B.S.", "field": "CS"}
            ],
        })

        parser = TxtNotesParser(ai_client=mock_client)
        result = parser.parse("Some recruiter notes about John Doe")

        assert result.name.display_name == "John Doe"
        assert result.name.first == "John"
        assert result.name.last == "Doe"
        assert result.contact is not None
        assert result.contact.emails[0].value == "john@example.com"
        assert result.contact.phones[0].value == "+1234567890"
        assert len(result.skills) == 2
        assert result.summary == "Strong candidate"
        assert len(result.experience) == 1
        assert len(result.education) == 1

    def test_parse_empty_text(self) -> None:
        """Empty text returns candidate with warning."""
        mock_client = MockGeminiClient()
        parser = TxtNotesParser(ai_client=mock_client)
        result = parser.parse("")

        assert result.metadata is not None
        warning_codes = [w.code for w in result.metadata.warnings]
        assert "EMPTY_INPUT" in warning_codes

    def test_parse_bytes_input(self) -> None:
        """Parser handles bytes input."""
        mock_client = MockGeminiClient(fixture={
            "name": "Jane",
            "skills": [],
            "experience": [],
            "education": [],
        })
        parser = TxtNotesParser(ai_client=mock_client)
        result = parser.parse(b"Notes about Jane")

        assert result.name.display_name == "Jane"

    def test_metadata_source_type(self) -> None:
        """Metadata includes txt_notes source type."""
        mock_client = MockGeminiClient()
        parser = TxtNotesParser(ai_client=mock_client)
        result = parser.parse("Some notes")

        assert result.metadata is not None
        assert "txt_notes" in result.metadata.source_types

    def test_ai_failure_returns_empty_candidate(self) -> None:
        """When AI extraction fails, parser returns empty with warning."""
        class FailingClient:
            def extract(self, text: str, prompt: str) -> dict:
                raise ValueError("Bad response")

        parser = TxtNotesParser(ai_client=FailingClient())  # type: ignore[arg-type]
        result = parser.parse("Some notes")

        assert result.metadata is not None
        warning_codes = [w.code for w in result.metadata.warnings]
        assert "AI_EXTRACTION_ERROR" in warning_codes
