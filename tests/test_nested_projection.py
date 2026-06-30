"""Tests for NestedProjectionEngine."""

from app.projections.nested_projection import NestedProjectionEngine


class TestNestedProjectionEngine:
    """Tests for the nested projection engine."""

    def setup_method(self) -> None:
        self.engine = NestedProjectionEngine()

    def test_sample_scenario(self) -> None:
        """Test the user-provided sample scenario."""
        data = {
            "id": "123",
            "details": {"email": "test@test.com", "phone": "999"},
            "tags": ["A", "B"],
            "metadata": {"source": "web"},
        }
        schema = {"details": {"email": True}, "tags": True}
        expected = {"details": {"email": "test@test.com"}, "tags": ["A", "B"]}

        result = self.engine.project(data, schema)
        assert result == expected

    def test_recursive_array_projection(self) -> None:
        """Test projecting a list of dictionaries."""
        data = {
            "jobs": [
                {"title": "Senior Engineer", "company": "Acme", "salary": 100},
                {"title": "Junior Engineer", "company": "Startup", "salary": 50},
            ]
        }
        schema = {"jobs": {"title": True, "company": True}}
        expected = {
            "jobs": [
                {"title": "Senior Engineer", "company": "Acme"},
                {"title": "Junior Engineer", "company": "Startup"},
            ]
        }

        result = self.engine.project(data, schema)
        assert result == expected

    def test_schema_false_filtering(self) -> None:
        """Test that False values in schema exclude data."""
        data = {"name": "John", "age": 30}
        schema = {"name": True, "age": False}
        expected = {"name": "John"}

        result = self.engine.project(data, schema)
        assert result == expected

    def test_mismatched_structures_return_none(self) -> None:
        """Test when data and schema structures mismatch."""
        data = "not a dict"
        schema = {"key": True}
        assert self.engine.project(data, schema) is None
