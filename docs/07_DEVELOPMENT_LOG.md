# Development Log

## Day 1 — Foundation

- [x] Create project specification document
- [x] Design architecture and pipeline
- [x] Create implementation plan
- [x] Establish AI usage policy
- [x] Define coding guidelines
- [x] Document design decisions
- [x] Create AI workflow documentation

---

## Day 2 — Core Models & Parsing

- [ ] Initialize Python project with `pyproject.toml`
- [ ] Configure `ruff`, `mypy`, `pytest`
- [ ] Define `CanonicalCandidate` Pydantic model
- [ ] Define `Provenance` and `ConfidenceScore` wrappers
- [ ] Define `SourceType` enum
- [ ] Implement `CandidateParser` protocol
- [ ] Implement `ParserFactory`
- [ ] Implement `CsvParser`
- [ ] Write model and parser tests
- [ ] Implement `JsonParser`
- [ ] Implement `XmlParser`

---

## Day 3 — AI Parsers

- [ ] Integrate Gemini API client
- [ ] Implement `PdfResumeParser`
- [ ] Implement `TxtNotesParser`
- [ ] Write extraction prompt for resumes
- [ ] Write extraction prompt for notes
- [ ] Write AI parser tests with sample documents
- [ ] Handle extraction failures gracefully

---

## Day 4 — Normalisation & Merge

- [ ] Implement phone normalizer
- [ ] Implement email normalizer
- [ ] Implement name normalizer
- [ ] Implement address normalizer
- [ ] Write normalizer tests
- [ ] Implement conflict detection rules
- [ ] Implement MergeEngine with source priority
- [ ] Implement confidence scoring per field
- [ ] Write merge and confidence tests

---

## Day 5 — Projection & Validation

- [ ] Define projection configuration schema
- [ ] Implement field mapping and transforms
- [ ] Implement ProjectionEngine
- [ ] Implement output SchemaValidator
- [ ] Write projection and validation tests

---

## Day 6 — API & Integration

- [ ] Implement FastAPI application
- [ ] Add `POST /transform` endpoint
- [ ] Wire full pipeline end-to-end
- [ ] Write API integration tests
- [ ] Performance profiling
- [ ] Error handling audit
- [ ] Final documentation pass
