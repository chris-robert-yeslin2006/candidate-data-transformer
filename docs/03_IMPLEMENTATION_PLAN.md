# Implementation Plan

## Phase 1 — Project Setup
- Initialize Python project with `pyproject.toml`
- Configure `ruff`, `mypy`, `pytest`
- Set up project directory structure
- Define dependencies (FastAPI, Pydantic, python-multipart, google-genai, python-pptx)

---

## Phase 2 — Canonical Model
- Define `CanonicalCandidate` Pydantic model
- Define `Provenance` and `ConfidenceScore` wrappers
- Define `SourceType` enum
- Write model tests

---

## Phase 3 — Parser Factory
- Define `CandidateParser` protocol/ABC
- Implement `ParserFactory` with source-type dispatch
- Register parsers via dependency injection
- Write factory tests

---

## Phase 4 — CSV Parser
- Implement `CsvParser` with `csv.DictReader`
- Map CSV columns to canonical fields
- Handle missing/empty values
- Write CSV parser tests

---

## Phase 5 — JSON / XML Parsers
- Implement `JsonParser`
- Implement `XmlParser`
- Map structured fields to canonical model
- Write parser tests

---

## Phase 6 — PDF Resume Parser
- Integrate Gemini API for resume extraction
- Define extraction prompt with structured output
- Parse Gemini response into `CanonicalCandidate`
- Handle extraction failures gracefully
- Write parser tests with sample resumes

---

## Phase 7 — TXT Notes Parser
- Integrate Gemini for free-form text extraction
- Define extraction prompt for notes
- Parse response into canonical model
- Write parser tests

---

## Phase 8 — Normalization Service
- Implement phone normalizer (strip non-digits, format E.164)
- Implement email normalizer (lowercase, trim whitespace)
- Implement name normalizer (capitalization, trim)
- Implement address normalizer (consistent format)
- Write normalizer tests

---

## Phase 9 — Merge Engine
- Implement source priority rules
- Implement conflict detection per field
- Apply tiebreakers (higher confidence, most recent, most complete)
- Preserve provenance through merge
- Write merge engine tests

---

## Phase 10 — Confidence Scoring
- Define confidence rules per field and per source
- Compute field-level confidence (0.0 – 1.0)
- Compute record-level confidence (aggregate)
- Attach scores to output
- Write confidence tests

---

## Phase 11 — Projection Engine
- Define projection configuration schema
- Implement field mapping and transform logic
- Support default values and computed fields
- Write projection engine tests

---

## Phase 12 — Schema Validation
- Define target schema as Pydantic model
- Validate projected output before delivery
- Return structured error messages on failure
- Write validation tests

---

## Phase 13 — API Layer
- Implement FastAPI application
- Add upload endpoint (`POST /transform`)
- Add projection configuration parameter
- Return transformed + validated output
- Write API integration tests

---

## Phase 14 — Testing & Optimization
- End-to-end pipeline tests with sample data
- Performance profiling and optimisation
- Error handling audit
- Documentation pass
