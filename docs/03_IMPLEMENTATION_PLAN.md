# Implementation Plan

## Phase 1 — Project Setup
- Initialize Python project with `pyproject.toml`
- Configure `ruff`, `mypy`, `pytest`
- Set up project directory structure
- Define dependencies (FastAPI, Pydantic, python-multipart, google-genai, PyMuPDF, python-dotenv)

---

## Phase 2 — Canonical Model
- Define `CanonicalCandidate` Pydantic model
- Define `Provenance` and `ConfidenceScore` models
- Define `SourceType` enum
- Define `CanonicalCandidateWithMeta` wrapper model
- Define `PipelineResult` response model
- Write model tests

---

## Phase 3 — Parser Factory
- Define `BaseParser` abstract class
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

## Phase 5 — Normalization Engine (Reader/Mapper Decoupling)

- Extract `CandidateMapper` from `CsvParser` private methods
- Define `Reader` abstract interface (`read(raw_data) -> Iterator[dict[str, str]]`)
- Implement `CsvReader` and `TSVReader` as concrete readers
- Adopt advanced column mapping schema with `required`, `type`, `default`, `transform` rules
- Retire monolithic `CsvParser` in favor of `Reader(CsvReader) + Mapper(CandidateMapper)` composition
- Write mapper and reader unit tests
- Update registry to accept `Reader` classes

---

## Phase 6 — ATS JSON Parser (Optional)
- Implement `AtsJsonParser`
- Map structured JSON fields to canonical model
- Handle missing/optional keys
- Write JSON parser tests

---

## Phase 7 — Gemini Client Interface
- Define `GeminiClient` abstract interface
- Implement `RealGeminiClient` (API key from env)
- Implement `MockGeminiClient` (deterministic fixtures)
- Write client tests with mock

---

## Phase 8 — PDF Resume Parser
- Extract text from PDF using PyMuPDF
- Pass text + extraction prompt to `GeminiClient`
- Parse structured JSON response into `CanonicalCandidate`
- Handle extraction failures gracefully (empty candidate + warning)
- Write parser tests with sample resumes (using `MockGeminiClient`)

---

## Phase 9 — TXT Notes Parser
- Pass raw text + extraction prompt to `GeminiClient`
- Parse structured JSON response into `CanonicalCandidate`
- Handle extraction failures gracefully
- Write parser tests (using `MockGeminiClient`)

---

## Phase 10 — Baseline Confidence Service
- Define baseline confidence rules per source type
- Compute baseline scores immediately after parsing
- Attach `ConfidenceScore` to `CanonicalCandidateWithMeta`
- Write baseline confidence tests

---

## Phase 11 — Normalization Service
- Implement phone normalizer (strip non-digits, format E.164)
- Implement email normalizer (lowercase, trim whitespace)
- Implement name normalizer (capitalization, trim)
- Implement address normalizer (consistent format)
- Write normalizer tests

---

## Phase 12 — Merge Engine
- Implement source priority rules
- Implement conflict detection per field
- Apply tiebreakers (source priority > baseline confidence > completeness > recency)
- Preserve provenance through merge
- Write merge engine tests

---

## Phase 13 — Refined Confidence Service
- Recalculate confidence post-merge
- Factors: cross-source agreement, completeness, extraction quality, normalization success, merge consistency
- Compute field-level and record-level refined scores
- Write refined confidence tests

---

## Phase 14 — Projection Engine
- Define projection configuration schema
- Implement field mapping and transform logic
- Support default values and computed fields
- Write projection engine tests

---

## Phase 15 — Schema Validation
- Define target schema as Pydantic model
- Validate projected output before delivery
- Return structured error messages on failure
- Write validation tests

---

## Phase 16 — PipelineService
- Implement `PipelineService` orchestrator
- Sequence: parse → baseline score → normalize → merge → refine → project → validate
- Collect warnings from partial failures
- Return `PipelineResult` with data + warnings + provenance
- Write PipelineService integration tests

---

## Phase 17 — API Layer
- Implement FastAPI application
- Add upload endpoint (`POST /transform`)
- Wire `PipelineService` as thin delegation
- Return `PipelineResult` as response
- Write API integration tests

---

## Phase 18 — Testing & Optimization
- End-to-end pipeline tests with sample data
- Performance profiling and optimisation
- Error handling audit
- Documentation pass
