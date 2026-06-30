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

- [ ] Implement `CsvParser`
- [ ] Implement `AtsJsonParser`
- [ ] Map structured fields to canonical model
- [ ] Handle missing/empty values
- [ ] Write parser tests

---

## Day 4 — Gemini Integration

- [ ] Define `GeminiClient` abstract interface
- [ ] Implement `RealGeminiClient`
- [ ] Implement `MockGeminiClient`
- [ ] Implement `PdfResumeParser` (PyMuPDF + Gemini)
- [ ] Implement `TxtNotesParser` (Gemini)
- [ ] Write extraction prompts for resumes and notes
- [ ] Write parser tests with `MockGeminiClient`

---

## Day 5 — Normalisation & Merge

- [ ] Implement baseline confidence scoring
- [ ] Implement phone normalizer
- [ ] Implement email normalizer
- [ ] Implement name normalizer
- [ ] Implement address normalizer
- [ ] Write normalizer tests
- [ ] Implement `MergeEngine` with source priority + baseline confidence tiebreakers
- [ ] Write merge engine tests

---

## Day 6 — Refined Confidence & Projection

- [ ] Implement refined confidence scoring
- [ ] Factors: cross-source agreement, completeness, extraction quality
- [ ] Write refined confidence tests
- [ ] Define projection configuration schema
- [ ] Implement `ProjectionService`
- [ ] Write projection tests
- [ ] Implement `ValidationService`
- [ ] Write validation tests

---

## Day 7 — PipelineService & API

- [ ] Implement `PipelineService` orchestrator
- [ ] Wire full pipeline end-to-end
- [ ] Collect warnings from partial failures
- [ ] Write PipelineService integration tests
- [ ] Implement FastAPI application
- [ ] Add `POST /transform` endpoint
- [ ] Write API integration tests

---

## Day 8 — Finalization

- [ ] End-to-end pipeline tests with sample data
- [ ] Performance profiling and optimisation
- [ ] Error handling audit
- [ ] Documentation pass
