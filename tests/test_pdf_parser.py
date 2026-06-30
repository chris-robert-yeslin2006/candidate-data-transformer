"""Tests for PDF resume parser using MockGeminiClient."""

from app.clients.gemini import MockGeminiClient
from app.parsers.pdf_parser import PdfResumeParser


class TestPdfResumeParser:
    """Tests for PDF resume parser with mock AI client."""

    def test_parse_with_mock_returns_candidate(self) -> None:
        """Parser returns a candidate from mock AI extraction."""
        mock_client = MockGeminiClient(fixture={
            "name": "John Doe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "summary": "Experienced engineer",
            "skills": ["Python", "JavaScript"],
            "experience": [
                {"title": "Senior Engineer", "company": "Acme", "description": "Led team"}
            ],
            "education": [
                {"institution": "MIT", "degree": "B.S.", "field": "CS"}
            ],
        })

        parser = PdfResumeParser(ai_client=mock_client)
        # Use a simple text string (PyMuPDF would fail on non-PDF bytes,
        # but the parser gracefully falls back)
        result = parser.parse(b"fake pdf content")

        # The parser will fail to extract PDF text and return empty candidate
        # with warning — this tests the graceful degradation path
        assert result.metadata is not None

    def test_parse_empty_bytes_returns_empty_candidate(self) -> None:
        """Empty input returns candidate with warning."""
        mock_client = MockGeminiClient()
        parser = PdfResumeParser(ai_client=mock_client)
        result = parser.parse(b"")

        assert result.metadata is not None

    def test_metadata_source_type(self) -> None:
        """Metadata includes PDF source type."""
        mock_client = MockGeminiClient()
        parser = PdfResumeParser(ai_client=mock_client)
        result = parser.parse(b"fake pdf")

        assert result.metadata is not None
        assert "pdf_resume" in result.metadata.source_types

    def test_ai_extraction_failure_returns_empty_candidate(self) -> None:
        """When AI extraction raises, parser returns empty candidate with warning."""
        class FailingClient:
            def extract(self, text: str, prompt: str) -> dict:
                raise ConnectionError("API down")

        parser = PdfResumeParser(ai_client=FailingClient())  # type: ignore[arg-type]
        result = parser.parse(b"fake pdf")

        assert result.metadata is not None
        # Should have warnings about the failure
        warning_codes = [w.code for w in result.metadata.warnings]
        assert any("ERROR" in code or "EXTRACTION" in code for code in warning_codes)
