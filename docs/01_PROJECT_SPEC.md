# Candidate Data Transformation Service

## Objective

Build a configurable candidate data transformation service capable of ingesting multiple heterogeneous data sources, normalizing them into a canonical candidate model, resolving conflicts, tracking provenance, and projecting the data into client-specific schemas.

---

## Functional Requirements

- Accept multiple input sources (CSV, PDF resumes, plain-text notes, JSON, XML)
- Support structured and unstructured data
- Convert all inputs into a canonical model
- Normalize candidate information (phone, email, address, name)
- Merge conflicting values from multiple sources
- Assign confidence scores at the field and record level
- Track provenance back to original source for every field
- Support runtime configurable output schemas
- Validate output against target schema before delivery

---

## Non Functional Requirements

- **Modular** — Each stage of the pipeline is an isolated, replaceable service
- **Extensible** — New parsers, normalizers, or output projections can be added without modifying existing code
- **Testable** — Every service has a single responsibility and can be tested in isolation
- **Explainable** — Pipeline decisions (merges, conflicts, confidence scores) are auditable
- **Deterministic** — Given the same inputs and configuration, the output is always identical
