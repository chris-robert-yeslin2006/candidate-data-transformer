"""
Shared test fixtures and configuration.

Provides pytest fixtures used across the test suite, including
mock clients, sample data (loaded from tests/fixtures/), and
application test helpers.

TODO: Add fixtures as tests are implemented.
"""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_csv_content() -> str:
    """Return CSV fixture content from tests/fixtures/."""
    return (FIXTURES_DIR / "sample_candidate.csv").read_text()


@pytest.fixture
def sample_resume_text() -> str:
    """Return resume text fixture from tests/fixtures/."""
    return (FIXTURES_DIR / "sample_resume.txt").read_text()
