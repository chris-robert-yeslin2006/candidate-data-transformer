"""
Confidence scoring service.

Provides baseline and refined confidence scoring for candidate data.
Baseline scores are source-based (assigned after parsing); refined
scores incorporate cross-source agreement, completeness, and merge
quality.
"""

from __future__ import annotations

import logging

from app.domain.models import CanonicalCandidate
from app.domain.models.confidence import Confidence
from app.domain.models.provenance import SourceType

logger = logging.getLogger(__name__)

# Baseline confidence scores per source type.
# Structured sources get higher baseline confidence.
BASELINE_SCORES: dict[SourceType, float] = {
    SourceType.CSV: 0.95,
    SourceType.ATS_JSON: 0.95,
    SourceType.PDF_RESUME: 0.80,
    SourceType.TXT_NOTES: 0.70,
    SourceType.LINKEDIN: 0.90,
    SourceType.GITHUB: 0.85,
    SourceType.WORKDAY: 0.95,
    SourceType.GREENHOUSE: 0.95,
    SourceType.LEVER: 0.95,
    SourceType.SUCCESSFACTORS: 0.95,
    SourceType.NAUKRI: 0.85,
    SourceType.INDEED: 0.85,
}


class ConfidenceService:
    """
    Computes baseline and refined confidence scores.

    Baseline scoring assigns an initial score based solely on
    source type reliability. Refined scoring recalculates after
    merge, incorporating cross-source agreement, completeness,
    and data quality factors.
    """

    def score_baseline(
        self,
        source_type: SourceType,
        candidate: CanonicalCandidate,
    ) -> Confidence:
        """
        Assign baseline confidence score based on source type.

        Args:
            source_type: The source type of the parsed data.
            candidate: The parsed candidate to score.

        Returns:
            Confidence object with baseline scores.
        """
        base_score = BASELINE_SCORES.get(source_type, 0.50)

        # Compute field-level scores
        fields: dict[str, float] = {}
        factors: dict[str, str] = {"source_type": str(source_type)}

        if candidate.name and candidate.name.display_name:
            fields["name"] = base_score
        if candidate.contact:
            if candidate.contact.emails:
                fields["email"] = base_score
            if candidate.contact.phones:
                fields["phone"] = base_score
        if candidate.skills:
            fields["skills"] = base_score
        if candidate.experience:
            fields["experience"] = base_score
        if candidate.education:
            fields["education"] = base_score
        if candidate.summary:
            fields["summary"] = base_score

        return Confidence(
            overall=base_score,
            fields=fields,
            factors=factors,
        )

    def score_refined(
        self,
        candidate: CanonicalCandidate,
        source_candidates: list[CanonicalCandidate],
        source_types: list[SourceType],
    ) -> Confidence:
        """
        Compute refined confidence score post-merge.

        Factors:
            - Cross-source agreement: fields with matching values
              from multiple sources get higher scores.
            - Completeness: percentage of fields populated.
            - Source diversity: more diverse sources increase confidence.

        Args:
            candidate: The merged candidate.
            source_candidates: List of pre-merge candidates from each source.
            source_types: Source types corresponding to each source candidate.

        Returns:
            Confidence object with refined scores.
        """
        factors: dict[str, str] = {}
        fields: dict[str, float] = {}

        # Factor 1: Completeness
        total_fields = 7  # name, email, phone, skills, experience, education, summary
        populated = 0
        if candidate.name and (candidate.name.display_name or candidate.name.first):
            populated += 1
        if candidate.contact and candidate.contact.emails:
            populated += 1
        if candidate.contact and candidate.contact.phones:
            populated += 1
        if candidate.skills:
            populated += 1
        if candidate.experience:
            populated += 1
        if candidate.education:
            populated += 1
        if candidate.summary:
            populated += 1

        completeness = populated / total_fields
        factors["completeness"] = f"{completeness:.2f}"

        # Factor 2: Source diversity
        unique_sources = len(set(source_types))
        diversity_bonus = min(unique_sources * 0.05, 0.15)
        factors["source_diversity"] = str(unique_sources)

        # Factor 3: Cross-source agreement for key fields
        agreement_score = self._compute_agreement(source_candidates)
        factors["cross_source_agreement"] = f"{agreement_score:.2f}"

        # Combine factors into overall score
        # Base from average of source baselines
        avg_baseline = 0.0
        if source_types:
            avg_baseline = sum(
                BASELINE_SCORES.get(st, 0.5) for st in source_types
            ) / len(source_types)

        overall = min(
            1.0,
            avg_baseline * 0.5  # 50% from source quality
            + completeness * 0.25  # 25% from completeness
            + agreement_score * 0.15  # 15% from cross-source agreement
            + diversity_bonus,  # up to 15% from diversity
        )

        # Field-level refined scores
        if candidate.name and (candidate.name.display_name or candidate.name.first):
            fields["name"] = min(1.0, overall + 0.05)
        if candidate.contact and candidate.contact.emails:
            fields["email"] = min(1.0, overall + 0.05)
        if candidate.contact and candidate.contact.phones:
            fields["phone"] = min(1.0, overall)
        if candidate.skills:
            fields["skills"] = min(1.0, overall - 0.05)
        if candidate.experience:
            fields["experience"] = min(1.0, overall)
        if candidate.education:
            fields["education"] = min(1.0, overall)
        if candidate.summary:
            fields["summary"] = min(1.0, overall - 0.05)

        return Confidence(
            overall=round(overall, 4),
            fields={k: round(v, 4) for k, v in fields.items()},
            factors=factors,
        )

    def _compute_agreement(
        self,
        source_candidates: list[CanonicalCandidate],
    ) -> float:
        """
        Compute cross-source agreement score.

        Checks how many key fields agree across sources.

        Args:
            source_candidates: List of candidates from different sources.

        Returns:
            Agreement score between 0.0 and 1.0.
        """
        if len(source_candidates) < 2:
            return 0.0

        agreements = 0
        comparisons = 0

        # Compare names
        names = [
            c.name.display_name.lower().strip()
            for c in source_candidates
            if c.name and c.name.display_name
        ]
        if len(names) >= 2:
            comparisons += 1
            if len(set(names)) == 1:
                agreements += 1

        # Compare emails
        emails: list[str] = []
        for c in source_candidates:
            if c.contact and c.contact.emails:
                emails.append(c.contact.emails[0].value.lower().strip())
        if len(emails) >= 2:
            comparisons += 1
            if len(set(emails)) == 1:
                agreements += 1

        # Compare phones (strip formatting for comparison)
        phones: list[str] = []
        for c in source_candidates:
            if c.contact and c.contact.phones:
                import re
                digits = re.sub(r"[^\d]", "", c.contact.phones[0].value)
                phones.append(digits)
        if len(phones) >= 2:
            comparisons += 1
            if len(set(phones)) == 1:
                agreements += 1

        if comparisons == 0:
            return 0.0

        return agreements / comparisons
