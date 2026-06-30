"""Tests for ConfidenceService."""

from app.domain.models import CanonicalCandidate, ContactInformation, Email, Phone, Skill
from app.domain.models.person_name import PersonName
from app.domain.models.provenance import SourceType
from app.services.confidence_service import ConfidenceService


class TestConfidenceService:
    """Tests for baseline and refined confidence scoring."""

    def setup_method(self) -> None:
        self.service = ConfidenceService()

    def test_baseline_csv(self) -> None:
        """CSV source gets 0.95 baseline."""
        candidate = CanonicalCandidate(
            name=PersonName(display_name="John Doe"),
        )
        conf = self.service.score_baseline(SourceType.CSV, candidate)
        assert conf.overall == 0.95

    def test_baseline_pdf(self) -> None:
        """PDF source gets 0.80 baseline."""
        candidate = CanonicalCandidate(
            name=PersonName(display_name="John Doe"),
        )
        conf = self.service.score_baseline(SourceType.PDF_RESUME, candidate)
        assert conf.overall == 0.80

    def test_baseline_txt(self) -> None:
        """TXT source gets 0.70 baseline."""
        candidate = CanonicalCandidate()
        conf = self.service.score_baseline(SourceType.TXT_NOTES, candidate)
        assert conf.overall == 0.70

    def test_baseline_field_scores(self) -> None:
        """Populated fields get field-level scores."""
        candidate = CanonicalCandidate(
            name=PersonName(display_name="John"),
            contact=ContactInformation(
                emails=[Email(value="john@example.com")],
            ),
            skills=[Skill(name="Python")],
        )
        conf = self.service.score_baseline(SourceType.CSV, candidate)

        assert "name" in conf.fields
        assert "email" in conf.fields
        assert "skills" in conf.fields

    def test_refined_single_source(self) -> None:
        """Refined scoring with single source."""
        candidate = CanonicalCandidate(
            name=PersonName(display_name="John"),
            contact=ContactInformation(
                emails=[Email(value="john@example.com")],
            ),
        )
        conf = self.service.score_refined(
            candidate,
            [candidate],
            [SourceType.CSV],
        )

        assert 0.0 < conf.overall <= 1.0
        assert "completeness" in conf.factors

    def test_refined_multiple_sources(self) -> None:
        """Refined scoring with multiple sources boosts confidence."""
        candidate = CanonicalCandidate(
            name=PersonName(display_name="John"),
            contact=ContactInformation(
                emails=[Email(value="john@example.com")],
                phones=[Phone(value="+1234567890")],
            ),
            skills=[Skill(name="Python")],
        )
        cand1 = CanonicalCandidate(
            name=PersonName(display_name="John"),
            contact=ContactInformation(
                emails=[Email(value="john@example.com")],
            ),
        )
        cand2 = CanonicalCandidate(
            name=PersonName(display_name="John"),
            contact=ContactInformation(
                emails=[Email(value="john@example.com")],
            ),
        )

        conf = self.service.score_refined(
            candidate,
            [cand1, cand2],
            [SourceType.CSV, SourceType.ATS_JSON],
        )

        assert conf.overall > 0.0
        assert "source_diversity" in conf.factors
        assert "cross_source_agreement" in conf.factors
