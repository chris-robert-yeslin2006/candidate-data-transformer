"""
Plain-text notes parser.

Uses an AI client to extract structured candidate information from
free-form recruiter notes or plain-text candidate profiles.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.clients.base import AiClient
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

# Extraction prompt for recruiter notes / plain text.
NOTES_EXTRACTION_PROMPT = """Extract structured candidate information from the following recruiter notes or plain text.
Return a JSON object with these exact keys:
{
    "name": "Full Name",
    "first_name": "First Name",
    "last_name": "Last Name",
    "email": "email@example.com",
    "phone": "+1234567890",
    "summary": "Brief summary of the candidate based on the notes",
    "skills": ["skill1", "skill2"],
    "experience": [
        {
            "title": "Job Title",
            "company": "Company Name",
            "description": "Brief description"
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
- If a field is not mentioned in the notes, use an empty string or empty list.
- Infer skills from context when they are mentioned indirectly.
- The notes may be informal — extract what you can."""


class TxtNotesParser(BaseParser):
    """
    Parser for plain-text candidate notes.

    Sends free-form text content to an AI client for semantic extraction of
    candidate fields. Designed for recruiter notes, interview summaries,
    and other unstructured text inputs.

    Depends on an AiClient abstraction for AI extraction, enabling
    unit testing with MockGeminiClient.
    """

    source_type: SourceType = SourceType.TXT_NOTES
    display_name: str = "Text Notes Parser"
    supported_extensions: list[str] = [".txt", ".md"]
    supported_mime_types: list[str] = ["text/plain"]
    requires_ai: bool = True
    parser_version: str = "1.0.0"

    def __init__(self, ai_client: AiClient) -> None:
        """
        Initialize the text notes parser.

        Args:
            ai_client: AiClient instance for AI extraction.
        """
        self._ai_client = ai_client
        logger.debug("TxtNotesParser initialized")

    def parse(self, raw_data: str | bytes, **kwargs: Any) -> CanonicalCandidate:
        """
        Parse plain-text notes into a CanonicalCandidate.

        Args:
            raw_data: Plain-text content as a string or bytes.
            **kwargs: Optional extraction parameters.

        Returns:
            CanonicalCandidate with parsed fields.

        Raises:
            ParsingError: If text extraction fails.
        """
        warnings: list[ProcessingWarning] = []

        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode("utf-8")

        text = raw_data.strip()

        if not text:
            warnings.append(
                ProcessingWarning(
                    message="Text input is empty",
                    source="txt_parser",
                    code="EMPTY_INPUT",
                    field="",
                )
            )
            candidate = CanonicalCandidate()
            candidate.metadata = ProcessingMetadata(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                parser_version=self.parser_version,
                source_types=[SourceType.TXT_NOTES],
                warnings=warnings,
            )
            return candidate

        candidate = self._ai_extract(text, warnings)

        candidate.metadata = ProcessingMetadata(
            created_at=datetime.now(),
            updated_at=datetime.now(),
            parser_version=self.parser_version,
            source_types=[SourceType.TXT_NOTES],
            warnings=warnings,
        )

        return candidate

    def _ai_extract(
        self,
        text: str,
        warnings: list[ProcessingWarning],
    ) -> CanonicalCandidate:
        """
        Use AI client to extract structured data from text notes.

        Args:
            text: Raw text content.
            warnings: Warning accumulator.

        Returns:
            CanonicalCandidate with extracted fields.
        """
        try:
            data = self._ai_client.extract(text, NOTES_EXTRACTION_PROMPT)
            return self._map_response(data)
        except (ConnectionError, ValueError) as exc:
            warnings.append(
                ProcessingWarning(
                    message=f"AI extraction failed: {exc}",
                    source="txt_parser",
                    code="AI_EXTRACTION_ERROR",
                    field="",
                )
            )
            return CanonicalCandidate()
        except NotImplementedError:
            warnings.append(
                ProcessingWarning(
                    message="AI client not implemented; returning empty candidate",
                    source="txt_parser",
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
