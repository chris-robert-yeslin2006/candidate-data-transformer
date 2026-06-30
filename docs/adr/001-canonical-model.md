# Title: ADR-001 — Canonical Model Design

## Decision
Define `CanonicalCandidate` as a Pydantic `BaseModel` aggregate root with nested value objects (`PersonName`, `ContactInformation`, `Location`, `PartialDate`) and entity collections (`skills`, `experience`, `education`, `certifications`, `projects`, `organizations`). Metadata (`ProcessingMetadata`) is embedded directly on the candidate rather than wrapped.

## Why
- Pydantic provides schema validation, serialization, and type safety out of the box.
- A single canonical model decouples downstream services (merge, normalisation, projection) from source-specific formats.
- Nesting value objects avoids a flat "stringly-typed" model while keeping field access ergonomic.

## Alternatives Considered
- **Flat dict representation** — rejected: no type safety, no validation, no self-documenting structure.
- **Generic wrapper (CanonicalCandidateWithMeta)** — rejected in favor of embedding metadata directly; simplifies downstream access patterns.
- **dataclasses** — rejected: Pydantic is already a project dependency for FastAPI and provides better validation ergonomics.

## Tradeoffs
- **Pro:** Strong typing catches field errors at the boundary; auto-generated JSON Schema for documentation.
- **Pro:** Nested value objects (e.g., `PersonName`) are reusable across the codebase.
- **Con:** Deeply nested models increase verbosity in field access (e.g., `candidate.contact.emails[0].value`).
- **Con:** Schema changes require coordinated updates to parsers, normalizers, and projection engine.

## Future Impact
- All parsers must produce `CanonicalCandidate` — this is the universal interface contract.
- Merge engine must compare field-by-field across candidate instances.
- Projection engine must read from `CanonicalCandidate` and transform to client schemas.
- `Provenanced<T>` generic wrapper exists for field-level provenance tracking but is not yet applied to every field — deferred to a future phase.
