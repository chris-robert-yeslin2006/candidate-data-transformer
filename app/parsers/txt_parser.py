"""
Plain-text notes parser.

Uses an AI client to extract structured candidate information from
free-form recruiter notes or plain-text candidate profiles.
Falls back to a placeholder keyword-based extraction when no AI client
is available.
"""

from __future__ import annotations

import logging
import re
import time
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
from app.parsers.context import ParserContext
from app.parsers.result import ParseResult

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

    Falls back to a placeholder keyword-based extraction when no AiClient
    is provided, making the parser usable in CLI or testing contexts
    without AI dependencies.

    Depends on an AiClient abstraction for AI extraction, enabling
    unit testing with MockGeminiClient.
    """

    source_type: SourceType = SourceType.TXT_NOTES
    display_name: str = "Text Notes Parser"
    supported_extensions: list[str] = [".txt", ".md"]
    supported_mime_types: list[str] = ["text/plain"]
    requires_ai: bool = True
    parser_version: str = "1.0.0"

    def __init__(self, ai_client: AiClient | None = None) -> None:
        """
        Initialize the text notes parser.

        Args:
            ai_client: Optional AiClient instance. If None, falls back
                       to placeholder keyword-based extraction.
        """
        self._ai_client = ai_client
        if ai_client is None:
            logger.info("TxtNotesParser initialized without AI client (placeholder mode)")
        else:
            logger.debug("TxtNotesParser initialized with AI client")

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

    def parse_with_context(self, context: ParserContext) -> ParseResult:
        """
        Parse plain-text notes from a ParserContext into a ParseResult.

        Args:
            context: ParserContext with text data and config.

        Returns:
            ParseResult wrapping the candidate and warnings.
        """
        start = time.time()
        if context.ai_client is not None:
            self._ai_client = context.ai_client

        warnings: list[ProcessingWarning] = []

        raw_data = context.raw_data
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
            duration = time.time() - start
            return ParseResult(
                candidate=CanonicalCandidate(),
                metadata=ProcessingMetadata(
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    parser_version=self.parser_version,
                    source_types=[str(context.source_type)],
                    processing_duration=duration,
                    warnings=warnings,
                ),
                warnings=warnings,
                parser_version=self.parser_version,
                source_types=[str(context.source_type)],
                processing_duration=duration,
            )

        candidate = self._ai_extract(text, warnings)

        duration = time.time() - start
        return ParseResult(
            candidate=candidate,
            metadata=ProcessingMetadata(
                created_at=datetime.now(),
                updated_at=datetime.now(),
                parser_version=self.parser_version,
                source_types=[str(context.source_type)],
                processing_duration=duration,
                warnings=warnings,
            ),
            warnings=warnings,
            parser_version=self.parser_version,
            source_types=[str(context.source_type)],
            processing_duration=duration,
        )

    def _ai_extract(
        self,
        text: str,
        warnings: list[ProcessingWarning],
    ) -> CanonicalCandidate:
        """
        Use AI client to extract structured data from text notes.

        Falls back to placeholder keyword-based extraction when
        no AI client is available.

        Args:
            text: Raw text content.
            warnings: Warning accumulator.

        Returns:
            CanonicalCandidate with extracted fields.
        """
        if self._ai_client is None:
            warnings.append(
                ProcessingWarning(
                    message="No AI client available; using placeholder extraction",
                    source="txt_parser",
                    code="PLACEHOLDER_EXTRACTION",
                    field="",
                )
            )
            return self._placeholder_extract(text)

        try:
            data = self._ai_client.extract(text, NOTES_EXTRACTION_PROMPT)
            return self._map_response(data)
        except (ConnectionError, ValueError) as exc:
            warnings.append(
                ProcessingWarning(
                    message=f"AI extraction failed; falling back to placeholder: {exc}",
                    source="txt_parser",
                    code="AI_EXTRACTION_ERROR",
                    field="",
                )
            )
            return self._placeholder_extract(text)
        except NotImplementedError:
            warnings.append(
                ProcessingWarning(
                    message="AI client not implemented; using placeholder extraction",
                    source="txt_parser",
                    code="AI_NOT_IMPLEMENTED",
                    field="",
                )
            )
            return self._placeholder_extract(text)

    def _placeholder_extract(self, text: str) -> CanonicalCandidate:
        """
        Keyword-based placeholder extraction when no AI client is available.

        Uses simple regex patterns to extract name, email, phone, and skills
        from plain text. Provides basic functionality for CLI/demo use
        without AI dependencies.

        Args:
            text: Raw text content.

        Returns:
            CanonicalCandidate with basic extracted fields.
        """
        candidate = CanonicalCandidate()

        # Extract email
        email_match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
        if email_match:
            candidate.contact = ContactInformation(
                emails=[Email(value=email_match.group(0), type="", is_primary=True)]
            )

        # Extract phone
        phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        if phone_match:
            if candidate.contact is None:
                candidate.contact = ContactInformation()
            candidate.contact.phones = [Phone(value=phone_match.group(0), type="", is_primary=True)]

        # Extract potential name from "Notes - Name" or "Name - Notes" pattern (avoid email matches)
        lines = text.strip().splitlines()
        name_match = re.search(r"(?:Recruiter\s+)?(?:Notes?|Candidate|Interview|Profile|Resume)?\s*[-:]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", text)
        if name_match:
            candidate.name = PersonName(display_name=name_match.group(1).strip())
        elif lines:
            first_line = lines[0].strip()
            # Only use first line as name if it looks like a real name (2-4 words, title case)
            words = first_line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                candidate.name = PersonName(display_name=first_line)

        # Extract skills (look for "Skills: ..." or "skills: ..." lines)
        skills_match = re.search(
            r"(?:skills|technologies|expertise)[:\s]+(.+?)(?:\n|$)",
            text, re.IGNORECASE,
        )
        if skills_match:
            raw = skills_match.group(1)
            for delim in ["|", ";", ","]:
                if delim in raw:
                    candidate.skills = [Skill(name=s.strip()) for s in raw.split(delim) if s.strip()]
                    break
            if not candidate.skills:
                candidate.skills = [Skill(name=raw.strip())]

        # Extract summary (first good descriptive sentence, not headers/labels)
        for line in lines:
            line = line.strip()
            if (line and not line.startswith("Recruiter") and not line.startswith("Skills")
                    and not line.startswith("Contact") and not line.startswith("Interviewed")
                    and len(line) > 30 and not line.startswith("Notes") and not line.startswith("Candidate")):
                candidate.summary = line
                break

        logger.info("Placeholder extraction completed for text (%d chars)", len(text))
        return candidate

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
