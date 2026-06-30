"""Tests for company templates (companya, companyb, companyc)."""

import os
from fastapi.testclient import TestClient

from app.main import create_app


class TestTemplates:
    """Tests for template resolution and mapping."""

    def setup_method(self) -> None:
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_template_files_exist(self) -> None:
        """Verify that company A, B, and C templates exist in the config folder."""
        for company in ["companya", "companyb", "companyc"]:
            path = os.path.join("config", f"{company}.json")
            assert os.path.exists(path), f"Template for {company} is missing"

    def test_transform_with_companya_template(self) -> None:
        """API transforms candidate data using companya template (name, email, skills)."""
        csv_content = b"name,email,phone,skills\nJohn Doe,john@example.com,555-123-4567,Python|React"

        response = self.client.post(
            "/api/v1/transform",
            files=[("files", ("test.csv", csv_content, "text/csv"))],
            data={
                "source_types": "csv",
                "projection_config": "companya",  # Requesting Company A template
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]

        # Company A asks for: full_name, email, skills
        assert data.get("full_name") == "John Doe"
        assert data.get("email") == "john@example.com"
        assert data.get("skills") == ["Python", "React"]

        # Company A does NOT ask for: phone or experience or summary
        assert "phone" not in data
        assert "experience" not in data

    def test_transform_with_companyb_template(self) -> None:
        """API transforms candidate data using companyb template."""
        csv_content = b"name,email,phone,title,company\nJane Doe,jane@example.com,555-987-6543,Lead Dev,Acme"

        response = self.client.post(
            "/api/v1/transform",
            files=[("files", ("test.csv", csv_content, "text/csv"))],
            data={
                "source_types": "csv",
                "projection_config": "companyb",  # Requesting Company B template
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]

        # Company B asks for: candidate_name, contact_email, contact_phone, work_history
        assert data.get("candidate_name") == "Jane Doe"
        assert data.get("contact_email") == "jane@example.com"
        assert data.get("contact_phone") == "+15559876543"
        assert len(data.get("work_history", [])) == 1
        assert data["work_history"][0].get("title") == "Lead Dev"

        # Company B does NOT ask for: skills
        assert "skills" not in data

    def test_transform_with_companyc_template(self) -> None:
        """API transforms candidate data using companyc template (skills only)."""
        csv_content = b"name,email,skills\nJohn Doe,john@example.com,Python|Rust"

        response = self.client.post(
            "/api/v1/transform",
            files=[("files", ("test.csv", csv_content, "text/csv"))],
            data={
                "source_types": "csv",
                "projection_config": "companyc",  # Company C template (skills list only)
            },
        )

        assert response.status_code == 200
        data = response.json()["data"]

        assert data.get("skills") == ["Python", "Rust"]
        assert "full_name" not in data
        assert "email" not in data

    def test_invalid_template_name_returns_400(self) -> None:
        """Requesting an invalid template name returns a 400 Bad Request."""
        csv_content = b"name,email\nJohn,john@example.com"

        response = self.client.post(
            "/api/v1/transform",
            files=[("files", ("test.csv", csv_content, "text/csv"))],
            data={
                "source_types": "csv",
                "projection_config": "invalidcompany",
            },
        )

        assert response.status_code == 400
        assert "Invalid projection_config" in response.json()["error"]
