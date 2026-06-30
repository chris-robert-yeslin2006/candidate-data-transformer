# Title: ADR-004 — CSV Parser Design

## Decision
Implement `CsvParser` as a `BaseParser` subclass using Python's `csv.DictReader`. It supports a configurable column mapping (default `DEFAULT_COLUMN_MAPPING`) that maps CSV header names to dotted field paths on `CanonicalCandidate`. The parser handles single-row extraction by design (multi-row CSV processing is deferred — see Tech Debt Item #1). Skill extraction supports multiple delimiters (`|`, `;`, `,`). Missing and unknown columns generate structured warnings rather than hard failures.

## Why
- `csv.DictReader` is stdlib — zero additional dependencies for the primary structured data parser.
- Column mapping decouples CSV column layout from the canonical model — clients with different CSV layouts use different mappings.
- Soft failures (warnings) align with the pipeline's graceful degradation strategy: a missing column in one CSV doesn't kill the entire pipeline.

## Alternatives Considered
- **Pandas-based parsing** — rejected: adds a heavy dependency (numpy + pandas) for a simple CSV reader; pandas is not currently a project dependency.
- **Hard-coded column index mapping** — rejected: fragile; breaks if the CSV column order changes.
- **AI-based CSV parsing** — rejected per AI usage policy: structured data parsing is deterministic and requires no LLM.

## Tradeoffs
- **Pro:** Column mapping is case-insensitive and supports aliases via duplicate mapping entries.
- **Pro:** 31 tests cover happy path, edge cases, custom mappings, skill delimiters, and warning generation.
- **Con:** Only the first data row is processed — multi-row CSV sources silently discard data (tracked as Tech Debt Item #1).
- **Con:** The private methods (`_set_nested_field`, `_parse_skill_list`, `_accumulate_experience`) are not reusable by other parsers (motivates the Reader/Mapper split in Phase 5).

## Future Impact
- `CsvParser` serves as the reference implementation for all tabular parsers.
- Skill parsing and experience accumulation logic will be extracted into a shared `CandidateMapper` (Phase 5).
- Column mapping will be upgraded from `dict[str, str]` to `dict[str, ColumnRule]` with validation rules (Tech Debt Item #2).
