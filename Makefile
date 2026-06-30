.PHONY: install run test lint format typecheck clean

install:
	uv sync

run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest

test-cov:
	uv run pytest --cov=app --cov-report=term-missing

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy .

clean:
	rm -rf .mypy_cache .pytest_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
