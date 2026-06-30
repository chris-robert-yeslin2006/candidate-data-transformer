# AI Usage Policy

## Principle

AI is used only where semantic understanding is required. All business rules remain deterministic and explainable.

## Component Usage Matrix

| Component               | AI Used | Reason |
|-------------------------|---------|--------|
| CSV Parsing             | ❌       | Structured format; deterministic parsing is sufficient |
| JSON / XML Parsing      | ❌       | Structured formats; standard library parsing is sufficient |
| Resume Extraction       | ✅ Gemini | Resume layouts vary widely and benefit from semantic extraction |
| TXT Notes Parsing       | ✅ Gemini | Free-form text is easier to interpret with an LLM |
| Phone Normalization     | ❌       | Existing libraries and regex are more reliable than AI |
| Email Validation        | ❌       | Regex and validators are deterministic and well-understood |
| Merge Engine            | ❌       | Business rules must be explainable and repeatable |
| Confidence Scoring      | ❌       | Confidence is based on explicit, deterministic rules |
| Projection Engine       | ❌       | Configuration-driven logic should remain deterministic |
| Schema Validation       | ❌       | Validation rules are fully specifiable in Pydantic schemas |

## Why This Policy Matters

- **Auditability** — Every merge decision and confidence score can be traced to a specific rule.
- **Testability** — Deterministic components require no LLM prompt tuning in tests.
- **Reliability** — Structured data parsing (CSV, JSON) has zero ambiguity; introducing AI adds unnecessary failure modes.
- **Cost** — LLM API calls are reserved for genuinely unstructured inputs where they provide clear value.
- **Latency** — Deterministic services execute in microseconds; AI calls add seconds. Minimising AI keeps the pipeline fast.

## Prompt Philosophy

When AI is used, prompts are engineered to produce structured, machine-parseable output. Prompts specify the exact schema to return so that parsing code is minimal and deterministic. Prompts are treated as first-class artifacts stored alongside the codebase.
