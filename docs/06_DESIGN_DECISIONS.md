# Design Decisions

## Why FastAPI?

Chosen because it provides automatic validation through Pydantic, excellent async support, and clear API documentation. It is the de facto standard for Python service APIs and aligns with the project's emphasis on type safety and validation.

---

## Why Pydantic?

Provides schema validation, serialization, and type safety out of the box. It eliminates an entire class of bugs (wrong types, missing fields) at the boundary. The canonical model, all configurations, and output schemas are Pydantic models.

---

## Why Parser Factory?

Allows new sources to be added without modifying existing parser implementations. Registration is configuration-driven, so the factory itself never needs a code change when a new parser arrives.

---

## Why Canonical Model?

Decouples downstream services from source-specific formats. The merge engine, normaliser, and projection engine all speak `CanonicalCandidate`. Adding JSON support tomorrow requires only a `JsonParser` — nothing downstream changes.

---

## Why PipelineService?

Keeps orchestration logic out of the API layer. The FastAPI endpoint is a thin transport layer: validate the request, call `PipelineService`, return the response. The service owns the workflow, handles partial failures, and collects warnings. Business logic never lives inside route handlers.

---

## Why Two-Phase Confidence?

A single confidence pass creates a circular dependency: the merge engine needs confidence for tiebreakers, but confidence scoring needs merge results for refinement. Splitting into **baseline** (pre-merge, source-based) and **refined** (post-merge, quality-based) resolves this cleanly. Baseline scores are coarse but sufficient for merge decisions; refined scores reflect the actual quality of the merged output.

---

## Why Rule-Based Merge?

Deterministic decisions are easier to explain, test, and audit than AI-generated merge logic. If we need to explain why a phone number was chosen over another, we point to a rule (source priority > baseline confidence > completeness > recency), not a model inference.

---

## Why AI Only for Resume and Notes Parsing?

Resume formats vary significantly (sections, layouts, missing data). LLMs outperform regex for extracting semantic information from unstructured documents. Conversely, structured data (CSV, JSON) has a known shape — parsing it with AI adds cost, latency, and non-determinism with zero benefit.

---

## Why Confidence Scoring?

Not all data is equally reliable. A phone number extracted by Gemini from a scanned PDF should carry less weight than one from a structured HR database. Confidence scores let downstream consumers make their own risk-based decisions.

---

## Why Provenance on Every Field?

Traceability is a hard requirement for any system that ingests from multiple sources. Every value in the final output can be traced back to "source X, line Y, extracted by Z". This is critical for debugging, auditing, and building trust.

---

## Why Projection Engine Instead of One Output Schema?

Different clients have different needs. One client might want `firstName`/`lastName`; another wants `fullName`. One wants E.164 phone numbers; another wants local format. A projection engine handles this at configuration time without code changes.

---

## Why GeminiClient Interface?

Dependency inversion makes AI-dependent parsers testable without real API calls. Unit tests use `MockGeminiClient` with deterministic JSON fixtures. Integration tests optionally use `RealGeminiClient` behind an environment flag. No parser ever reads `os.environ["GEMINI_API_KEY"]` directly — the client is injected.

---

## Why Graceful Degradation on Parse Failure?

An unreachable Gemini API or a malformed CSV should not take down the entire pipeline. Every parser catches its own errors and returns an empty/partial candidate with a warning. `PipelineService` collects warnings and continues with whatever sources succeeded. The API response includes both the merged output and the warnings array.

---

## Why Remove PPTX Support?

PowerPoint files are outside the assignment scope. Including `python-pptx` as a dependency would add maintenance surface without a use case. The architecture remains open for future parsers through the factory pattern — adding a `PptxParser` later requires no changes to existing code.

---

---

## Why Decouple Ingestion from Mapping?

The current monolithic parser violates single responsibility — a single class reads raw bytes, interprets column headers, and populates the canonical model. Splitting into **Readers** (format-specific) and **CandidateMapper** (format-agnostic) makes each layer independently testable and allows adding new tabular formats (TSV, Excel, Google Sheets) without touching transformation logic. See the "Future Architecture" section in `ARCHITECTURE.md` for the full plan.

---

## Why a Rule-Based Column Mapping Schema?

The current flat mapping (`dict[str, str]`) supports basic column renaming but cannot express validation rules, type coercion, or conditional transformations. A nested rule-based schema (see `TECH_DEBT.md` Item #2) adds `required`, `type`, `default`, and `transform` — enabling the same mapping configuration to serve both validation and transformation without code changes.

---

## Why Confidence + Provenance as Metadata Rather Than Fields?

Metadata is attached to, but separate from, business data. This keeps the canonical model clean — merge and projection logic operates on candidate data without caring about the metadata wrapper, while audit tools can inspect it.
