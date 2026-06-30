# Current Status

## Current Branch
feature/normalization-engine

## Last Completed Phase
Phase 5 — Reader / Mapper Architecture

## Merged
- Phase 1 — Project Setup
- Phase 2 — Canonical Model
- Phase 3 — Parser Framework
- Phase 4 — CSV Parser
- Phase 5 — Reader / Mapper Architecture

## In Progress
None

## Next Phase
Phase 6 — Normalization Framework

## Architectural Decisions
- `CanonicalCandidate` is the aggregate root.
- Registry is frozen after startup.
- `SourceType` uses `StrEnum`.
- CSV parser is the reference implementation.
- `Provenanced<T>` exists but is not yet applied to every field.
- `PipelineResult` will replace `ProcessingMetadata` on Candidate in a later phase.
- Tabular formats are split into Reader (format-specific I/O) and CandidateMapper (format-agnostic transformation).
- `CSVRecord` is the seam between Reader and Mapper — a frozen dataclass with zero domain knowledge.
- `CSVReader` is reusable for TSV via `delimiter="\t"`.

## Deferred Work
- Gemini client (RealGeminiClient.extract)
- Merge Engine
- Projection Engine
- Schema Validation
- Confidence Services (Baseline + Refined)
- Normalization Services (phone, email, name, address)
- ATS JSON Parser
- PDF Resume Parser
- TXT Notes Parser
- POST /transform endpoint
- Advanced column mapping with ColumnRule (Tech Debt Item #2)
