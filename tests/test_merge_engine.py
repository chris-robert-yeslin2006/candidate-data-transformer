"""Tests for MergeEngine."""

from app.domain.models import (
    CanonicalCandidate,
    ContactInformation,
    Education,
    Email,
    Experience,
    Phone,
    Skill,
)
from app.domain.models.organization import Organization
from app.domain.models.person_name import PersonName
from app.domain.models.provenance import SourceType
from app.services.merge_engine import MergeEngine


class TestMergeEngine:
    """Tests for candidate merge engine."""

    def setup_method(self) -> None:
        self.engine = MergeEngine()

    def test_merge_empty_list(self) -> None:
        """Merging empty list returns empty candidate."""
        merged, warnings = self.engine.merge([], [])
        assert merged.name.display_name == ""

    def test_merge_single_candidate(self) -> None:
        """Single candidate returns itself."""
        candidate = CanonicalCandidate(
            name=PersonName(display_name="John Doe"),
        )
        merged, warnings = self.engine.merge([candidate], [SourceType.CSV])
        assert merged.name.display_name == "John Doe"

    def test_merge_name_from_higher_priority(self) -> None:
        """Name comes from higher-priority source."""
        csv_candidate = CanonicalCandidate(
            name=PersonName(display_name="John from CSV"),
        )
        json_candidate = CanonicalCandidate(
            name=PersonName(display_name="John from JSON"),
        )

        # ATS_JSON has priority 1, CSV has priority 2
        merged, warnings = self.engine.merge(
            [csv_candidate, json_candidate],
            [SourceType.CSV, SourceType.ATS_JSON],
        )
        assert merged.name.display_name == "John from JSON"

    def test_merge_skills_union(self) -> None:
        """Skills are merged as union, deduplicated."""
        cand1 = CanonicalCandidate(
            skills=[Skill(name="Python"), Skill(name="JavaScript")],
        )
        cand2 = CanonicalCandidate(
            skills=[Skill(name="Python"), Skill(name="SQL")],
        )

        merged, warnings = self.engine.merge(
            [cand1, cand2],
            [SourceType.CSV, SourceType.ATS_JSON],
        )
        skill_names = [s.name for s in merged.skills]
        assert "Python" in skill_names
        assert "JavaScript" in skill_names
        assert "SQL" in skill_names
        # Python should not be duplicated
        assert skill_names.count("Python") == 1

    def test_merge_emails_dedup(self) -> None:
        """Emails are merged with deduplication."""
        cand1 = CanonicalCandidate(
            contact=ContactInformation(
                emails=[Email(value="john@example.com", is_primary=True)],
            ),
        )
        cand2 = CanonicalCandidate(
            contact=ContactInformation(
                emails=[
                    Email(value="john@example.com"),
                    Email(value="john.work@company.com"),
                ],
            ),
        )

        merged, warnings = self.engine.merge(
            [cand1, cand2],
            [SourceType.CSV, SourceType.ATS_JSON],
        )
        assert merged.contact is not None
        assert len(merged.contact.emails) == 2

    def test_merge_experience_dedup(self) -> None:
        """Experience entries are deduplicated by title+company."""
        cand1 = CanonicalCandidate(
            experience=[
                Experience(
                    title="Senior Engineer",
                    organization=Organization(name="Acme"),
                )
            ],
        )
        cand2 = CanonicalCandidate(
            experience=[
                Experience(
                    title="Senior Engineer",
                    organization=Organization(name="Acme"),
                ),
                Experience(
                    title="Junior Engineer",
                    organization=Organization(name="StartupXYZ"),
                ),
            ],
        )

        merged, warnings = self.engine.merge(
            [cand1, cand2],
            [SourceType.CSV, SourceType.ATS_JSON],
        )
        assert len(merged.experience) == 2

    def test_merge_education_dedup(self) -> None:
        """Education entries are deduplicated."""
        cand1 = CanonicalCandidate(
            education=[Education(institution="MIT", degree="B.S.")],
        )
        cand2 = CanonicalCandidate(
            education=[Education(institution="MIT", degree="B.S.")],
        )

        merged, warnings = self.engine.merge(
            [cand1, cand2],
            [SourceType.CSV, SourceType.ATS_JSON],
        )
        assert len(merged.education) == 1

    def test_merge_summary_from_priority(self) -> None:
        """Summary comes from highest-priority source."""
        cand1 = CanonicalCandidate(summary="CSV summary")
        cand2 = CanonicalCandidate(summary="JSON summary")

        merged, warnings = self.engine.merge(
            [cand1, cand2],
            [SourceType.CSV, SourceType.ATS_JSON],
        )
        # ATS_JSON has higher priority
        assert merged.summary == "JSON summary"
