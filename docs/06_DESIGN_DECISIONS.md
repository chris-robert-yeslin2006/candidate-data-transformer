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

## Why Rule-Based Merge?

Deterministic decisions are easier to explain, test, and audit than AI-generated merge logic. If we need to explain why a phone number was chosen over another, we point to a rule (source priority > confidence > recency), not a model inference.

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

## Why Confidence + Provenance as Metadata Rather Than Fields?

Metadata is attached to, but separate from, business data. This keeps the canonical model clean — merge and projection logic operates on candidate data without caring about the metadata wrapper, while audit tools can inspect it.
