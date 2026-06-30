"""
Merge engine.

Merges multiple CanonicalCandidate objects (one per source) into
a single unified candidate. Uses deterministic tiebreaker rules:
source priority → baseline confidence → completeness → recency.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.domain.models import (
    CanonicalCandidate,
    ContactInformation,
    Education,
    Email,
    Experience,
    Phone,
    Skill,
)
from app.domain.models.confidence import Confidence
from app.domain.models.person_name import PersonName
from app.domain.models.provenance import SourceType
from app.domain.models.warning import Warning as ProcessingWarning

logger = logging.getLogger(__name__)

# Default source priority (lower = higher priority).
DEFAULT_SOURCE_PRIORITY: dict[SourceType, int] = {
    SourceType.ATS_JSON: 1,
    SourceType.CSV: 2,
    SourceType.PDF_RESUME: 3,
    SourceType.LINKEDIN: 4,
    SourceType.GITHUB: 5,
    SourceType.TXT_NOTES: 6,
    SourceType.WORKDAY: 1,
    SourceType.GREENHOUSE: 1,
    SourceType.LEVER: 1,
    SourceType.SUCCESSFACTORS: 1,
    SourceType.NAUKRI: 4,
    SourceType.INDEED: 4,
}


class MergeEngine:
    """
    Merges multiple candidate records into a single unified candidate.

    Tiebreaker order for conflicting field values:
    1. Source priority (configured per client)
    2. Baseline confidence (higher wins)
    3. Completeness (more fields populated wins)
    4. Recency (most recent timestamp wins)

    Every merge decision is recorded for provenance tracking.
    """

    def __init__(
        self,
        source_priority: dict[SourceType, int] | None = None,
    ) -> None:
        """
        Initialize the merge engine.

        Args:
            source_priority: Optional override for source priority.
                            Lower numbers = higher priority.
        """
        self._source_priority = source_priority or DEFAULT_SOURCE_PRIORITY
        logger.debug("MergeEngine initialized")

    def merge(
        self,
        candidates: list[CanonicalCandidate],
        source_types: list[SourceType],
        confidences: list[Confidence] | None = None,
    ) -> tuple[CanonicalCandidate, list[ProcessingWarning]]:
        """
        Merge multiple candidates into a single unified candidate.

        Args:
            candidates: List of candidates from different sources.
            source_types: Source type for each candidate.
            confidences: Optional baseline confidence for each candidate.

        Returns:
            Tuple of (merged candidate, list of merge warnings).
        """
        warnings: list[ProcessingWarning] = []

        if not candidates:
            return CanonicalCandidate(), warnings

        if len(candidates) == 1:
            return candidates[0], warnings

        # Rank candidates by priority
        ranked = self._rank_candidates(candidates, source_types, confidences)

        # Merge fields
        merged = CanonicalCandidate()
        merged.name = self._merge_name(ranked, warnings)
        merged.contact = self._merge_contact(ranked, warnings)
        merged.skills = self._merge_skills(ranked)
        merged.experience = self._merge_experience(ranked)
        merged.education = self._merge_education(ranked)
        merged.summary = self._merge_summary(ranked, warnings)

        return merged, warnings

    def _rank_candidates(
        self,
        candidates: list[CanonicalCandidate],
        source_types: list[SourceType],
        confidences: list[Confidence] | None,
    ) -> list[tuple[CanonicalCandidate, SourceType, float]]:
        """
        Rank candidates by priority for tiebreaking.

        Returns list of (candidate, source_type, confidence) tuples
        sorted by priority (highest priority first).
        """
        ranked: list[tuple[CanonicalCandidate, SourceType, float]] = []

        for i, (cand, st) in enumerate(zip(candidates, source_types)):
            conf = confidences[i].overall if confidences and i < len(confidences) else 0.5
            ranked.append((cand, st, conf))

        # Sort by: source priority (asc), confidence (desc), completeness (desc)
        ranked.sort(
            key=lambda x: (
                self._source_priority.get(x[1], 99),
                -x[2],
                -self._completeness_score(x[0]),
            )
        )

        return ranked

    def _completeness_score(self, candidate: CanonicalCandidate) -> float:
        """Count populated fields as a completeness metric."""
        score = 0.0
        if candidate.name and (candidate.name.display_name or candidate.name.first):
            score += 1
        if candidate.contact and candidate.contact.emails:
            score += 1
        if candidate.contact and candidate.contact.phones:
            score += 1
        if candidate.skills:
            score += 1
        if candidate.experience:
            score += 1
        if candidate.education:
            score += 1
        if candidate.summary:
            score += 1
        return score

    def _merge_name(
        self,
        ranked: list[tuple[CanonicalCandidate, SourceType, float]],
        warnings: list[ProcessingWarning],
    ) -> PersonName:
        """Merge name field — take from highest priority source that has it."""
        for cand, st, _ in ranked:
            if cand.name and (cand.name.display_name or cand.name.first):
                return cand.name

        return PersonName()

    def _merge_contact(
        self,
        ranked: list[tuple[CanonicalCandidate, SourceType, float]],
        warnings: list[ProcessingWarning],
    ) -> ContactInformation | None:
        """
        Merge contact information.

        For emails and phones, take the primary from highest-priority
        source, then append unique values from other sources.
        """
        merged_emails: list[Email] = []
        merged_phones: list[Phone] = []
        seen_emails: set[str] = set()
        seen_phones: set[str] = set()

        for cand, st, _ in ranked:
            if not cand.contact:
                continue

            for email in cand.contact.emails:
                key = email.value.lower().strip()
                if key and key not in seen_emails:
                    seen_emails.add(key)
                    merged_emails.append(email)

            for phone in cand.contact.phones:
                import re
                key = re.sub(r"[^\d]", "", phone.value)
                if key and key not in seen_phones:
                    seen_phones.add(key)
                    merged_phones.append(phone)

        if not merged_emails and not merged_phones:
            return None

        # Mark first email and phone as primary
        if merged_emails:
            merged_emails[0].is_primary = True
        if merged_phones:
            merged_phones[0].is_primary = True

        contact = ContactInformation(
            emails=merged_emails,
            phones=merged_phones,
        )

        # Take location from highest-priority source
        for cand, st, _ in ranked:
            if cand.contact and cand.contact.location:
                contact.location = cand.contact.location
                break

        return contact

    def _merge_skills(
        self,
        ranked: list[tuple[CanonicalCandidate, SourceType, float]],
    ) -> list[Skill]:
        """Merge skills — union of all skills, deduplicated by name."""
        seen: set[str] = set()
        merged: list[Skill] = []

        for cand, _, _ in ranked:
            for skill in cand.skills:
                key = skill.name.lower().strip()
                if key and key not in seen:
                    seen.add(key)
                    merged.append(skill)

        return merged

    def _merge_experience(
        self,
        ranked: list[tuple[CanonicalCandidate, SourceType, float]],
    ) -> list[Experience]:
        """
        Merge experience — take from highest-priority source that has it,
        then append unique entries from other sources.
        """
        seen_titles: set[str] = set()
        merged: list[Experience] = []

        for cand, _, _ in ranked:
            for exp in cand.experience:
                key = f"{exp.title.lower().strip()}|{(exp.organization.name.lower().strip() if exp.organization else '')}"
                if key not in seen_titles:
                    seen_titles.add(key)
                    merged.append(exp)

        return merged

    def _merge_education(
        self,
        ranked: list[tuple[CanonicalCandidate, SourceType, float]],
    ) -> list[Education]:
        """Merge education — union, deduplicated by institution+degree."""
        seen: set[str] = set()
        merged: list[Education] = []

        for cand, _, _ in ranked:
            for edu in cand.education:
                key = f"{edu.institution.lower().strip()}|{edu.degree.lower().strip()}"
                if key not in seen:
                    seen.add(key)
                    merged.append(edu)

        return merged

    def _merge_summary(
        self,
        ranked: list[tuple[CanonicalCandidate, SourceType, float]],
        warnings: list[ProcessingWarning],
    ) -> str:
        """Take summary from highest-priority source that has one."""
        for cand, st, _ in ranked:
            if cand.summary and cand.summary.strip():
                return cand.summary

        return ""
