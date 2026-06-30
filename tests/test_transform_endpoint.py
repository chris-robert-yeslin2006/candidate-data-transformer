"""Tests for the /transform API endpoint."""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


class TestTransformEndpoint:
    """Tests for POST /api/v1/transform and /api/v1/transform/json."""

    def setup_method(self) -> None:
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_health_check(self) -> None:
        """Health check returns healthy status."""
        response = self.client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_transform_csv_upload(self) -> None:
        """Upload a CSV file for transformation."""
        csv_content = b"name,email,phone\nJohn Doe,john@example.com,555-123-4567"

        response = self.client.post(
            "/api/v1/transform",
            files=[("files", ("test.csv", csv_content, "text/csv"))],
            data={"source_types": "csv"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"].get("full_name") == "John Doe"
        assert "confidence" in data
        assert "warnings" in data
        assert "provenance" in data

    def test_transform_json_upload(self) -> None:
        """Upload a JSON file for transformation."""
        json_content = json.dumps({
            "name": "Jane Smith",
            "email": "jane@example.com",
            "skills": ["Python", "SQL"],
        }).encode("utf-8")

        response = self.client.post(
            "/api/v1/transform",
            files=[("files", ("test.json", json_content, "application/json"))],
            data={"source_types": "ats_json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"].get("full_name") == "Jane Smith"

    def test_transform_no_files(self) -> None:
        """No files returns 400 error."""
        response = self.client.post("/api/v1/transform")
        assert response.status_code == 400

    def test_transform_json_body(self) -> None:
        """Transform using JSON body endpoint."""
        response = self.client.post(
            "/api/v1/transform/json",
            json={
                "sources": [
                    {
                        "source_type": "csv",
                        "raw_data": "name,email\nJohn,john@example.com",
                        "source_id": "inline.csv",
                    }
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"].get("full_name") == "John"

    def test_transform_json_body_no_sources(self) -> None:
        """Empty sources list returns 400."""
        response = self.client.post(
            "/api/v1/transform/json",
            json={"sources": []},
        )
        assert response.status_code == 400

    def test_transform_multi_source(self) -> None:
        """Upload CSV + JSON for multi-source merge."""
        csv_content = b"name,email,skills\nJohn Doe,john@example.com,Python|SQL"
        json_content = json.dumps({
            "name": "John Doe",
            "phone": "+15551234567",
            "skills": ["Python", "React"],
            "summary": "Engineer",
        }).encode("utf-8")

        response = self.client.post(
            "/api/v1/transform",
            files=[
                ("files", ("data.csv", csv_content, "text/csv")),
                ("files", ("data.json", json_content, "application/json")),
            ],
            data={"source_types": "csv,ats_json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"].get("full_name") == "John Doe"
        assert len(data["provenance"]) == 2

    def test_transform_auto_detect_extension(self) -> None:
        """Source type auto-detected from file extension."""
        csv_content = b"name,email\nJohn,john@example.com"

        response = self.client.post(
            "/api/v1/transform",
            files=[("files", ("candidates.csv", csv_content, "text/csv"))],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"].get("full_name") == "John"

    def test_transform_with_projection_config(self) -> None:
        """Custom projection config via form data."""
        csv_content = b"name,email\nJohn Doe,john@example.com"
        proj_config = json.dumps({
            "fields": {
                "candidate_name": "name.display_name",
                "contact_email": "contact.emails[0].value",
            }
        })

        response = self.client.post(
            "/api/v1/transform",
            files=[("files", ("test.csv", csv_content, "text/csv"))],
            data={
                "source_types": "csv",
                "projection_config": proj_config,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"].get("candidate_name") == "John Doe"
        assert "full_name" not in data["data"]

    def test_gui_samples_endpoint(self) -> None:
        """Verify the gui samples helper endpoint lists samples."""
        response = self.client.get("/api/v1/gui/samples")
        assert response.status_code == 200
        data = response.json()
        assert "samples" in data
        assert isinstance(data["samples"], list)
        if len(data["samples"]) > 0:
            sample = data["samples"][0]
            assert "name" in sample
            assert "content" in sample
            assert "source_type" in sample

    def test_gui_templates_endpoint(self) -> None:
        """Verify the gui templates helper endpoint lists config templates."""
        response = self.client.get("/api/v1/gui/templates")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)
        if len(data["templates"]) > 0:
            tpl = data["templates"][0]
            assert "name" in tpl
            assert "filename" in tpl
            assert "content" in tpl

    def test_gui_root_endpoint(self) -> None:
        """Verify that accessing root / serves the HTML visual console."""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Candidate Data Transformer" in response.text

