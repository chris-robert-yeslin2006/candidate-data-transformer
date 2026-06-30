"""End-to-end pipeline tests with sample data."""

import json

from app.domain.models.provenance import SourceType
from app.services.pipeline_service import PipelineService


class TestPipelineE2E:
    """End-to-end tests for the full transformation pipeline."""

    def setup_method(self) -> None:
        # Import here to use the fully-wired default registry
        from app.parsers import default_registry
        from app.parsers.registry import ParserFactory

        parser_factory = ParserFactory(
            registry=default_registry,
            default_ai_client=None,
        )
        self.pipeline = PipelineService(parser_factory=parser_factory)

    def test_csv_single_source(self) -> None:
        """Process a single CSV file end-to-end."""
        csv_data = "name,email,phone,skills\nJohn Doe,john@example.com,(555) 123-4567,Python|JavaScript"

        result = self.pipeline.process(
            files=[{
                "raw_data": csv_data,
                "source_type": SourceType.CSV,
                "source_id": "test.csv",
            }]
        )

        assert result.data.get("full_name") == "John Doe"
        assert result.data.get("email") == "john@example.com"
        assert result.data.get("phone") == "+15551234567"  # Normalized
        assert "Python" in result.data.get("skills", [])
        assert result.confidence.overall > 0.0
        assert len(result.provenance) == 1
        assert result.provenance[0] == "csv"

    def test_json_single_source(self) -> None:
        """Process a single JSON file end-to-end."""
        json_data = json.dumps({
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "+1-555-987-6543",
            "skills": ["Python", "React", "AWS"],
            "summary": "Full-stack engineer",
        })

        result = self.pipeline.process(
            files=[{
                "raw_data": json_data,
                "source_type": SourceType.ATS_JSON,
                "source_id": "test.json",
            }]
        )

        assert result.data.get("full_name") == "Jane Smith"
        assert result.data.get("email") == "jane@example.com"
        assert len(result.data.get("skills", [])) == 3
        assert result.data.get("summary") == "Full-stack engineer"

    def test_csv_and_json_merge(self) -> None:
        """Process CSV + JSON and merge."""
        csv_data = "name,email,skills\nJohn Doe,john@example.com,Python|SQL"
        json_data = json.dumps({
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+15551234567",
            "skills": ["Python", "JavaScript", "React"],
            "summary": "Senior engineer",
        })

        result = self.pipeline.process(
            files=[
                {
                    "raw_data": csv_data,
                    "source_type": SourceType.CSV,
                    "source_id": "csv_source",
                },
                {
                    "raw_data": json_data,
                    "source_type": SourceType.ATS_JSON,
                    "source_id": "json_source",
                },
            ]
        )

        # Name should be present
        assert result.data.get("full_name") == "John Doe"
        # Email from both sources (same)
        assert result.data.get("email") == "john@example.com"
        # Phone from JSON source
        assert result.data.get("phone") is not None
        # Skills should be union
        skills = result.data.get("skills", [])
        assert "Python" in skills
        assert "SQL" in skills
        assert "JavaScript" in skills
        assert "React" in skills
        # Summary from JSON
        assert result.data.get("summary") == "Senior engineer"
        # Both sources in provenance
        assert len(result.provenance) == 2
        # Confidence should be boosted by multiple sources
        assert result.confidence.overall > 0.0

    def test_empty_files_list(self) -> None:
        """Processing no files returns empty result."""
        result = self.pipeline.process(files=[])

        assert result.data == {}
        assert result.is_valid is False

    def test_malformed_csv_generates_warning(self) -> None:
        """Malformed CSV generates parse warning but doesn't crash."""
        result = self.pipeline.process(
            files=[{
                "raw_data": "",
                "source_type": SourceType.CSV,
                "source_id": "empty.csv",
            }]
        )

        # Should have warnings
        assert len(result.warnings) > 0

    def test_unknown_source_type(self) -> None:
        """Unknown source type string generates warning."""
        result = self.pipeline.process(
            files=[{
                "raw_data": "some data",
                "source_type": "unknown_format",
                "source_id": "test",
            }]
        )

        warning_codes = [w.code for w in result.warnings]
        assert "UNKNOWN_SOURCE_TYPE" in warning_codes

    def test_custom_projection_config(self) -> None:
        """Custom projection config maps fields differently."""
        csv_data = "name,email\nJohn Doe,john@example.com"

        result = self.pipeline.process(
            files=[{
                "raw_data": csv_data,
                "source_type": SourceType.CSV,
            }],
            projection_config={
                "fields": {
                    "candidate_name": "name.display_name",
                    "contact_email": "contact.emails[0].value",
                },
            },
        )

        assert result.data.get("candidate_name") == "John Doe"
        assert result.data.get("contact_email") == "john@example.com"
        assert "full_name" not in result.data

    def test_processing_duration_tracked(self) -> None:
        """Pipeline tracks processing duration."""
        csv_data = "name,email\nJohn,john@example.com"

        result = self.pipeline.process(
            files=[{
                "raw_data": csv_data,
                "source_type": SourceType.CSV,
            }]
        )

        assert result.processing_duration >= 0.0

    def test_result_serialization(self) -> None:
        """PipelineResult serializes to dict correctly."""
        csv_data = "name,email\nJohn,john@example.com"

        result = self.pipeline.process(
            files=[{
                "raw_data": csv_data,
                "source_type": SourceType.CSV,
            }]
        )

        result_dict = result.to_dict()
        assert "data" in result_dict
        assert "confidence" in result_dict
        assert "warnings" in result_dict
        assert "provenance" in result_dict
        assert "processing_duration" in result_dict
        assert "is_valid" in result_dict
