"""
PDF resume parser.

Extracts text from PDF documents and uses an AI client to semantically
extract structured candidate information. Handles the wide variety
of resume layouts that rule-based extraction cannot reliably parse.
Falls back to returning the raw extracted text when no AI client is
available.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.clients.base import AiClient
from app.core.exceptions import ParsingError
from app.domain.models import (
    CanonicalCandidate,
    ContactInformation,
    Education,
    Email,
    Experience,
    Phone,
    Skill,
)
from app.domain.models.metadata import ProcessingMetadata
from app.domain.models.organization import Organization
from app.domain.models.person_name import PersonName
from app.domain.models.provenance import SourceType
from app.domain.models.warning import Warning as ProcessingWarning
from app.parsers.base import BaseParser

logger = logging.getLogger(__name__)

# Extraction prompt sent to Gemini along with the PDF text.
RESUME_EXTRACTION_PROMPT = """Extract structured candidate information from the following resume text.
Return a JSON object with these exact keys:
{
    "name": "Full Name",
    "first_name": "First Name",
    "last_name": "Last Name",
    "email": "email@example.com",
    "phone": "+1234567890",
    "summary": "Professional summary or objective",
    "skills": ["skill1", "skill2"],
    "experience": [
        {
            "title": "Job Title",
            "company": "Company Name",
            "description": "Job description or responsibilities"
        }
    ],
    "education": [
        {
            "institution": "University Name",
            "degree": "Degree Name",
            "field": "Field of Study"
        }
    ]
}

Rules:
- Return ONLY valid JSON, no extra text.
- If a field is not found in the resume, use an empty string or empty list.
- Extract ALL skills mentioned, including tools and technologies.
- Extract ALL work experiences, most recent first.
- Extract ALL education entries."""


class PdfResumeParser(BaseParser):
    """
    Parser for PDF-format resumes.

    Uses a two-stage extraction process:
    1. Extract raw text from the PDF using PyMuPDF.
    2. Send extracted text to an AI client for semantic parsing into
       structured candidate data.

    Depends on an AiClient abstraction for AI extraction, enabling
    unit testing with MockGeminiClient.
    """

    source_type: SourceType = SourceType.PDF_RESUME
    display_name: str = "PDF Resume Parser"
    supported_extensions: list[str] = [".pdf"]
    supported_mime_types: list[str] = ["application/pdf"]
    requires_ai: bool = True
    parser_version: str = "1.0.0"

    def __init__(self, ai_client: AiClient | None = None) -> None:
        """
        Initialize the PDF resume parser.

        Args:
            ai_client: Optional AiClient instance. If None, falls back
                       to returning raw extracted text.
        """
        self._ai_client = ai_client
        if ai_client is None:
            logger.info("PdfResumeParser initialized without AI client (placeholder mode)")
        else:
            logger.debug("PdfResumeParser initialized")

    def parse(self, raw_data: str | bytes, **kwargs: Any) -> CanonicalCandidate:
        """
        Parse a PDF resume into a CanonicalCandidate.

        Args:
            raw_data: PDF file content as bytes.
            **kwargs: Optional extraction parameters.

        Returns:
            CanonicalCandidate with parsed fields.

        Raises:
            ParsingError: If the PDF cannot be read or extraction fails.
        """
        warnings: list[ProcessingWarning] = []

        # Stage 1: Extract text from PDF
        text = self._extract_text(raw_data, warnings)

        if not text.strip():
            warnings.append(
                ProcessingWarning(
                    message="PDF contains no extractable text",
                    source="pdf_parser",
                    code="EMPTY_PDF",
                    field="",
                )
            )
            candidate = CanonicalCandidate()
            candidate.metadata = ProcessingMetadata(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                parser_version=self.parser_version,
                source_types=[SourceType.PDF_RESUME],
                warnings=warnings,
            )
            return candidate

        # Stage 2: AI extraction
        candidate = self._ai_extract(text, warnings)

        candidate.metadata = ProcessingMetadata(
            created_at=datetime.now(),
            updated_at=datetime.now(),
            parser_version=self.parser_version,
            source_types=[SourceType.PDF_RESUME],
            warnings=warnings,
        )

        return candidate

    def _extract_text(
        self,
        raw_data: str | bytes,
        warnings: list[ProcessingWarning],
    ) -> str:
        """
        Extract text content from a PDF file using PyMuPDF.

        Args:
            raw_data: PDF content as bytes or string path.
            warnings: Warning accumulator.

        Returns:
            Extracted text from all pages.
        """
        if isinstance(raw_data, str):
            raw_data = raw_data.encode("utf-8")

        try:
            import fitz  # PyMuPDF

            doc = fitz.open(stream=raw_data, filetype="pdf")
            pages: list[str] = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                pages.append(page.get_text())
            doc.close()
            return "\n".join(pages)
        except ImportError:
            warnings.append(
                ProcessingWarning(
                    message="PyMuPDF not installed; cannot extract PDF text",
                    source="pdf_parser",
                    code="MISSING_DEPENDENCY",
                    field="",
                )
            )
            return ""
        except Exception as exc:
            warnings.append(
                ProcessingWarning(
                    message=f"Failed to extract text from PDF: {exc}",
                    source="pdf_parser",
                    code="PDF_EXTRACTION_ERROR",
                    field="",
                )
            )
            return ""

    def _ai_extract(
        self,
        text: str,
        warnings: list[ProcessingWarning],
    ) -> CanonicalCandidate:
        """
        Use AI client to extract structured data from resume text.

        Falls back to a placeholder candidate with raw text when
        no AI client is available.

        Args:
            text: Extracted PDF text.
            warnings: Warning accumulator.

        Returns:
            CanonicalCandidate with extracted fields.
        """
        if self._ai_client is None:
            warnings.append(
                ProcessingWarning(
                    message="No AI client available; returning raw text as summary",
                    source="pdf_parser",
                    code="PLACEHOLDER_EXTRACTION",
                    field="",
                )
            )
            candidate = CanonicalCandidate()
            candidate.summary = text[:2000]
            return candidate

        try:
            data = self._ai_client.extract(text, RESUME_EXTRACTION_PROMPT)
            return self._map_response(data)
        except (ConnectionError, ValueError) as exc:
            warnings.append(
                ProcessingWarning(
                    message=f"AI extraction failed: {exc}",
                    source="pdf_parser",
                    code="AI_EXTRACTION_ERROR",
                    field="",
                )
            )
            return CanonicalCandidate()
        except NotImplementedError:
            warnings.append(
                ProcessingWarning(
                    message="AI client not implemented; returning empty candidate",
                    source="pdf_parser",
                    code="AI_NOT_IMPLEMENTED",
                    field="",
                )
            )
            return CanonicalCandidate()

    def _map_response(self, data: dict[str, Any]) -> CanonicalCandidate:
        """
        Map AI extraction response to CanonicalCandidate.

        Args:
            data: Structured JSON from AI extraction.

        Returns:
            Populated CanonicalCandidate.
        """
        candidate = CanonicalCandidate()

        # Name
        name = PersonName()
        name.display_name = str(data.get("name", "")).strip()
        name.first = str(data.get("first_name", "")).strip()
        name.last = str(data.get("last_name", "")).strip()
        candidate.name = name

        # Contact
        contact = ContactInformation()
        email = str(data.get("email", "")).strip()
        phone = str(data.get("phone", "")).strip()
        if email:
            contact.emails = [Email(value=email, type="", is_primary=True)]
        if phone:
            contact.phones = [Phone(value=phone, type="", is_primary=True)]
        if contact.emails or contact.phones:
            candidate.contact = contact

        # Summary
        candidate.summary = str(data.get("summary", "")).strip()

        # Skills
        raw_skills = data.get("skills", [])
        if isinstance(raw_skills, list):
            candidate.skills = [
                Skill(name=str(s).strip())
                for s in raw_skills
                if str(s).strip()
            ]

        # Experience
        raw_experiences = data.get("experience", [])
        if isinstance(raw_experiences, list):
            for exp in raw_experiences:
                if isinstance(exp, dict):
                    title = str(exp.get("title", "")).strip()
                    company = str(exp.get("company", "")).strip()
                    description = str(exp.get("description", "")).strip()
                    candidate.experience.append(
                        Experience(
                            title=title,
                            organization=Organization(name=company) if company else None,
                            description=description,
                        )
                    )

        # Education
        raw_education = data.get("education", [])
        if isinstance(raw_education, list):
            for edu in raw_education:
                if isinstance(edu, dict):
                    candidate.education.append(
                        Education(
                            institution=str(edu.get("institution", "")).strip(),
                            degree=str(edu.get("degree", "")).strip(),
                            field=str(edu.get("field", "")).strip(),
                        )
                    )

        return candidate
