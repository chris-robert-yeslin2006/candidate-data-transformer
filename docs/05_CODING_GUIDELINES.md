# Coding Guidelines

## Design Principles

- **Single Responsibility Principle** — Every class and function has exactly one reason to change.
- **Open / Closed Principle** — Modules are open for extension but closed for modification.
- **Separation of Concerns** — Parsing, normalisation, merging, and projection are independent layers.
- **Composition over Inheritance** — Prefer small, composable services over deep class hierarchies.
- **Deterministic Business Rules** — All transformations produce the same output for the same input.
- **Strong Typing** — Use Pydantic models and type hints throughout; avoid `dict` and `Any` where the shape is known.
- **Dependency Injection** — Pass dependencies explicitly rather than instantiating them inside services.
- **Small, Focused Services** — Each service is independently testable with no hidden state.

---

## General Rules

- No God classes. A class that does everything does nothing well.
- No duplicated business logic. Extract shared logic into a dedicated service.
- One responsibility per service. If a class has two unrelated methods, split it.
- Every parser returns a canonical model. No parser-specific output formats leak downstream.
- Every service is independently testable. Mock external dependencies; test business logic with real inputs.
- Configuration over hard-coding. Client-specific logic belongs in config, not in code.
- Fail fast. Validate inputs at the boundary; raise clear errors early.
- No bare exceptions. Catch specific exception types; handle or re-raise with context.

---

## Naming Conventions

- **Files** — `snake_case.py`, matching the primary class/function.
- **Classes** — `PascalCase`.
- **Functions & Methods** — `snake_case`.
- **Constants** — `UPPER_SNAKE_CASE`.
- **Private members** — Prefix with `_`.

---

## Testing Guidelines

- One test file per source file.
- Test the public API, not implementation details.
- Use realistic sample data for parsers (real CSV files, sample resumes).
- Test edge cases: empty inputs, missing fields, malformed data, duplicate records.
- Integration tests verify the full pipeline; unit tests verify individual services.
