# Multi-Source Candidate Data Transformer

Engineering Assignment for Eightfold Internship.

## Status

Under Development

## Documentation

See `/docs` for:

- Project Specification
- Architecture
- AI Usage & Disclosure
- Design Decisions
- Implementation Plan
- Development Log

## Tech Stack

- Python 3.12
- FastAPI
- Pydantic
- PyMuPDF
- Gemini API
- Pytest

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Run tests
pytest

# Start the API
uvicorn app.main:app --reload
```
