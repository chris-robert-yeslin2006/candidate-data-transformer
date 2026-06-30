"""Tests for ProjectionService."""

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
from app.projections.projection_service import ProjectionService


class TestProjectionService:
    """Tests for projection engine."""

    def setup_method(self) -> None:
        self.service = ProjectionService()

    def test_default_projection(self) -> None:
        """Default projection maps standard fields."""
        candidate = CanonicalCandidate(
            name=PersonName(display_name="John Doe", first="John", last="Doe"),
            contact=ContactInformation(
                emails=[Email(value="john@example.com")],
                phones=[Phone(value="+15551234567")],
            ),
            skills=[Skill(name="Python"), Skill(name="JavaScript")],
            summary="Experienced engineer",
            experience=[
                Experience(
                    title="Senior Engineer",
                    organization=Organization(name="Acme"),
                    description="Led team",
                )
            ],
            education=[
                Education(institution="MIT", degree="B.S.", field="CS")
            ],
        )

        result, warnings = self.service.project(candidate)

        assert result["full_name"] == "John Doe"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["email"] == "john@example.com"
        assert result["phone"] == "+15551234567"
        assert result["skills"] == ["Python", "JavaScript"]
        assert result["summary"] == "Experienced engineer"
        assert len(result["experience"]) == 1
        assert len(result["education"]) == 1

    def test_custom_projection_config(self) -> None:
        """Custom config maps only specified fields."""
        candidate = CanonicalCandidate(
            name=PersonName(display_name="John Doe"),
            summary="Engineer",
        )

        config = {
            "fields": {
                "candidate_name": "name.display_name",
                "bio": "summary",
            }
        }

        result, warnings = self.service.project(candidate, config)

        assert result["candidate_name"] == "John Doe"
        assert result["bio"] == "Engineer"
        assert "full_name" not in result

    def test_missing_fields_excluded(self) -> None:
        """Fields without values are excluded from output."""
        candidate = CanonicalCandidate(
            name=PersonName(display_name="John"),
        )

        result, warnings = self.service.project(candidate)

        assert "full_name" in result
        assert "email" not in result
        assert "phone" not in result

    def test_defaults_applied(self) -> None:
        """Default values are applied when field is missing."""
        candidate = CanonicalCandidate()

        config = {
            "fields": {
                "status": "nonexistent_path",
            },
            "defaults": {
                "status": "unknown",
            },
        }

        result, warnings = self.service.project(candidate, config)
        assert result["status"] == "unknown"

    def test_empty_candidate(self) -> None:
        """Empty candidate produces minimal output."""
        candidate = CanonicalCandidate()
        result, warnings = self.service.project(candidate)

        # Should have no populated fields
        assert len(result) == 0 or all(v is None for v in result.values())
