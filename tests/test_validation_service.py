"""Tests for ValidationService."""

from app.projections.validation_service import ValidationService


class TestValidationService:
    """Tests for schema validation service."""

    def setup_method(self) -> None:
        self.service = ValidationService()

    def test_valid_output(self) -> None:
        """Valid output passes validation."""
        output = {"full_name": "John Doe", "email": "john@example.com"}
        is_valid, warnings = self.service.validate(output)

        assert is_valid is True
        assert len(warnings) == 0

    def test_missing_required_field(self) -> None:
        """Missing required field fails validation."""
        output = {"email": "john@example.com"}
        schema = {"required": ["full_name"]}

        is_valid, warnings = self.service.validate(output, schema)

        assert is_valid is False
        assert any(w.code == "MISSING_REQUIRED_FIELD" for w in warnings)

    def test_empty_required_field(self) -> None:
        """Empty required field fails validation."""
        output = {"full_name": "", "email": "john@example.com"}
        schema = {"required": ["full_name"]}

        is_valid, warnings = self.service.validate(output, schema)

        assert is_valid is False
        assert any(w.code == "EMPTY_REQUIRED_FIELD" for w in warnings)

    def test_type_mismatch(self) -> None:
        """Type mismatch generates warning."""
        output = {"full_name": "John", "skills": "Python"}
        schema = {
            "required": ["full_name"],
            "types": {"skills": "list"},
        }

        is_valid, warnings = self.service.validate(output, schema)

        assert is_valid is False
        assert any(w.code == "TYPE_MISMATCH" for w in warnings)

    def test_correct_types_pass(self) -> None:
        """Correct types pass validation."""
        output = {
            "full_name": "John",
            "skills": ["Python"],
            "experience": [{"title": "Engineer"}],
        }
        schema = {
            "required": ["full_name"],
            "types": {
                "skills": "list",
                "experience": "array",
            },
        }

        is_valid, warnings = self.service.validate(output, schema)

        assert is_valid is True
        assert len(warnings) == 0

    def test_no_schema_uses_default(self) -> None:
        """No schema uses default required fields."""
        output = {"full_name": "John"}
        is_valid, warnings = self.service.validate(output)

        assert is_valid is True
