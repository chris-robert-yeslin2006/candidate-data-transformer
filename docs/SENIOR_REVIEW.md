# Senior Review Notes

Architectural and design-level review notes for each phase.

---

## Phase 1 Review — Project Setup
**Status:** Approved

No architectural concerns. Standard Python project bootstrap.

---

## Phase 2 Review — Canonical Model
**Status:** Approved

Observations:
- `Provenanced[T]` generic is defined but not yet applied to every field. Will need to be wired through all parsers in a later phase. This is acceptable for now as the CSV parser only logs warnings rather than per-field provenance.
- `ProcessingMetadata` embedded on `CanonicalCandidate` is a temporary measure. A `PipelineResult` wrapper (candidate + provenance trail + warnings) is expected to replace it once the full pipeline is wired.

---

## Phase 3 Review — Parser Factory
**Status:** Approved

Observations:
- Registry freeze at startup is correct — prevents runtime configuration drift.
- Factory DI via `inspect.signature` is pragmatic for the current scope. If the parser ecosystem grows beyond 5-6 parsers, consider explicit dependency declarations over reflection.
- The `default_registry` in `__init__.py` should be reviewed for thread safety if the factory is ever used concurrently (currently single-threaded at startup).

---

## Phase 4 Review — CSV Parser
**Status:** Approved

### Future Improvements Tracker
The following improvements were identified but deferred to maintain scope discipline:

1. **Reader / Mapper Split (Phase 5)**
   - Extract `CandidateMapper` from `CsvParser` private methods
   - Define `Reader` abstract interface for format-specific ingestion
   - Define `ColumnRule` Pydantic model for typed column mapping
   - See Tech Debt Item #1 and Architecture section "Decouple Ingestion from Mapping"

2. **ParseResult Return Type**
   - Currently parsers embed `ProcessingMetadata` on the candidate
   - A future `ParseResult` wrapper should separate candidate data from parsing metadata and warnings
   - This would make the `parse()` return type more explicit and easier to chain in the pipeline

3. **ParserContext Adoption**
   - `ParserContext` model exists but is unused
   - Should be adopted to standardize parse parameters (raw_data, source_type, filename, etc.)
   - Will reduce signature variation across parsers

4. **Plugin Architecture**
   - The registry supports plugin-style registration
   - Future: parsers could be loaded from external packages via entry points
   - Not currently needed but should be designed for if the parser ecosystem grows

---

## Phase 5 Review — Reader / Mapper Architecture
**Status:** Approved

### Completed
The monolithic `CsvParser` has been split into three single-responsibility components:

- **`CSVReader`** — format-specific I/O (encoding, BOM, delimiter)
- **`CSVRecord`** — immutable data seam (frozen dataclass)
- **`CandidateMapper`** — format-agnostic field mapping (column mapping, warnings, nested fields)

`CsvParser` is now a thin orchestrator: read → map → attach metadata.

### Architectural Observations

1. **Single Responsibility Achieved.** Each class has exactly one reason to change. CSVReader changes when CSV format handling changes; CandidateMapper changes when the canonical model changes.

2. **Extensibility Proof.** Adding TSV support is now a one-liner: `CSVReader(delimiter="\t")`. The CandidateMapper is reused unchanged. Adding Excel requires only a new Reader that produces CSVRecord objects — no mapping logic duplicated.

3. **Backward Compatibility.** The CsvParser public API (`__init__(column_mapping)`, `parse(raw_data, **kwargs)`) is unchanged. All 34 existing tests pass without modification.

4. **Latent Bug Fixed.** The original `_build_header_map` used `h.strip() not in header_map` for unknown column detection, which falsely flagged whitespace-padded headers that had been successfully matched. The new implementation uses a normalized lookup set, eliminating these false `UNKNOWN_COLUMN` warnings.

5. **No Abstract Reader Interface Yet.** Phase 5 intentionally omits a formal `Reader` ABC. The current `CSVReader` is concrete. A formal `Reader` interface will be extracted when a second reader (TSVReader or ExcelReader) is introduced in a future phase. Premature abstraction would create indirection without a second implementation to validate it.

### Future Items Still Deferred

- Advanced column mapping with `ColumnRule` (Tech Debt Item #2)
- `ParseResult` return type for `parse()` methods
- `ParserContext` adoption
- Formal `Reader` ABC (defer until a second reader exists)
