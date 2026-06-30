# Architecture

## Pipeline Overview

```
                INPUTS
                   │
                   ▼
            Parser Factory
                   │
                   ▼
          Source Parsers
                   │
                   ▼
        Canonical Candidate
                   │
                   ▼
           Normalization
                   │
                   ▼
        Conflict Resolution
                   │
                   ▼
      Confidence + Provenance
                   │
                   ▼
      Config Projection Engine
                   │
                   ▼
           Schema Validation
                   │
                   ▼
             Final Output
```

---

## Parser Factory

### Responsibility
Select the appropriate parser for each input source based on file type, MIME type, or format hint.

### Input
Uploaded file or raw data string with type metadata.

### Output
Concrete parser instance (CSV, PDF, TXT, JSON, XML).

### Why?
Keeps parser selection logic isolated. Supports the Open/Closed Principle — adding a `LinkedInParser` requires no changes to existing parsers or the factory itself.

---

## Source Parsers

### Responsibility
Convert a source-specific format into the canonical candidate model.

### Input
Raw file content (bytes or string).

### Output
A `CanonicalCandidate` object with provenance metadata attached to each field.

### Why?
Each parser encapsulates the extraction logic for one format. CSV parsing is regex/rule-based; resume parsing delegates to Gemini for semantic extraction. This separation means format-specific edge cases never leak into downstream services.

---

## Canonical Candidate

### Responsibility
Define the universal data model that every parser produces and every downstream service consumes.

### Input
(Internal — the model is instantiated by parsers.)

### Output
A strongly-typed Pydantic model with optional provenance wrappers on every field.

### Why?
Decouples source-specific formats from pipeline logic. Adding a new data source requires only a new parser; the merge engine, normalizers, and projection engine remain unchanged.

---

## Normalization

### Responsibility
Transform raw field values into a consistent, standardised format.

### Input
A `CanonicalCandidate` with raw values.

### Output
A `CanonicalCandidate` with normalised values.

### Why?
Parsers extract data as-is from the source. Normalisation applies rules (phone format, email lowercase, address components) so downstream services compare apples to apples.

---

## Conflict Resolution

### Responsibility
When multiple sources provide values for the same field, apply deterministic rules to reconcile discrepancies.

### Input
List of `CanonicalCandidate` objects (one per source).

### Output
A single merged `CanonicalCandidate` with the resolved value and provenance.

### Why?
Merge decisions must be explainable and repeatable. Rule-based logic (source priority, confidence score, timestamp precedence) is auditable. AI-generated merge logic is opaque and non-deterministic.

---

## Confidence + Provenance

### Responsibility
Assign a confidence score to every field and record, and track which source produced each value.

### Input
Merged `CanonicalCandidate` with source metadata.

### Output
A `CanonicalCandidate` with `ConfidenceScore` and `Provenance` on each field.

### Why?
Consumer applications need to know how reliable each piece of data is. Provenance provides an audit trail. Confidence enables downstream systems to make risk-based decisions.

---

## Config Projection Engine

### Responsibility
Transform the canonical model into a client-specific output schema at runtime based on a projection configuration.

### Input
`CanonicalCandidate` + projection configuration (field mappings, transforms, defaults).

### Output
Dictionary or Pydantic model matching the target schema.

### Why?
Different clients require different fields, formats, and naming conventions. A projection engine avoids building one-off endpoints. Configuration-driven means no code changes for new client schemas.

---

## Schema Validation

### Responsibility
Validate the projected output against the target schema before delivery.

### Input
Projected output + target schema definition.

### Output
Validated output or structured validation errors.

### Why?
Catches projection misconfiguration, missing required fields, and type mismatches before data reaches the client. Fail fast, fail clearly.
