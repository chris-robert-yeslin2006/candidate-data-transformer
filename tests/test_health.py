"""
Health check endpoint tests.

Verifies the FastAPI application boots correctly and the health
check route returns the expected response.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    """GET /api/v1/health should return healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert data["service"] == "candidate-transformer"
