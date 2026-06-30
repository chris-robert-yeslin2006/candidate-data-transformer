# Development Log

## Day 1 — Foundation

- [x] Create project specification document
- [x] Design architecture and pipeline
- [x] Create implementation plan
- [x] Establish AI usage policy
- [x] Define coding guidelines
- [x] Document design decisions
- [x] Create AI workflow documentation
- [x] Initialize git repository and push to GitHub

---

## Day 2 — Core Models & Factory

- [ ] Initialize Python project with `pyproject.toml`
- [ ] Configure `ruff`, `mypy`, `pytest`
- [ ] Define `CanonicalCandidate` Pydantic model
- [ ] Define `Provenance` and `ConfidenceScore` models
- [ ] Define `CanonicalCandidateWithMeta` wrapper
- [ ] Define `PipelineResult` response model
- [ ] Define `SourceType` enum
- [ ] Implement `BaseParser` abstract class
- [ ] Implement `ParserFactory` with source-type dispatch
- [ ] Write model and factory tests

---

## Day 3 — Structured Parsers

- [x] Implement `CsvParser` with `csv.DictReader`, default column mapping, skill delimiters
- [x] Handle missing/empty values, unknown columns, malformed CSV, BOM, null bytes
- [x] Generate `MISSING_COLUMN` / `UNKNOWN_COLUMN` warnings with provenance metadata
- [x] Write 31 CSV parser unit tests (happy path, edge cases, skills, warnings, column mapping)
- [ ] Implement `AtsJsonParser`
- [ ] Map structured fields to canonical model
- [ ] Handle missing/empty values
- [ ] Write parser tests

---

## Day 4 — Reader/Mapper Decoupling & Column Mapping Schema

- [ ] Extract `CandidateMapper` from `CsvParser` private methods
- [ ] Define `Reader` abstract interface
- [ ] Implement `CsvReader` and `TSVReader`
- [ ] Implement `ColumnRule` Pydantic model for advanced mapping
- [ ] Update parser registry for Reader/Mapper composition
- [ ] Write mapper and reader unit tests

---

## Day 5 — Gemini Integration

- [ ] Define `GeminiClient` abstract interface
- [ ] Implement `RealGeminiClient`
- [ ] Implement `MockGeminiClient`
- [ ] Implement `PdfResumeParser` (PyMuPDF + Gemini)
- [ ] Implement `TxtNotesParser` (Gemini)
- [ ] Write extraction prompts for resumes and notes
- [ ] Write parser tests with `MockGeminiClient`

---

## Day 6 — Normalisation & Merge

- [ ] Implement baseline confidence scoring
- [ ] Implement phone normalizer
- [ ] Implement email normalizer
- [ ] Implement name normalizer
- [ ] Implement address normalizer
- [ ] Write normalizer tests
- [ ] Implement `MergeEngine` with source priority + baseline confidence tiebreakers
- [ ] Write merge engine tests

---

## Day 7 — Refined Confidence & Projection

- [ ] Implement refined confidence scoring
- [ ] Factors: cross-source agreement, completeness, extraction quality
- [ ] Write refined confidence tests
- [ ] Define projection configuration schema
- [ ] Implement `ProjectionService`
- [ ] Write projection tests
- [ ] Implement `ValidationService`
- [ ] Write validation tests

---

## Day 8 — PipelineService & API

- [ ] Implement `PipelineService` orchestrator
- [ ] Wire full pipeline end-to-end
- [ ] Collect warnings from partial failures
- [ ] Write PipelineService integration tests
- [ ] Implement FastAPI application
- [ ] Add `POST /transform` endpoint
- [ ] Write API integration tests

---

## Day 9 — Finalization

- [ ] End-to-end pipeline tests with sample data
- [ ] Performance profiling and optimisation
- [ ] Error handling audit
- [ ] Documentation pass
