# Tech Debt Backlog

Items identified during development that are out of scope for the current phase but tracked for future sprints.

---

## Item #1: Decouple Ingestion from Mapping (Reader/Mapper Split)

**Priority:** High  
**Target Phase:** Phase 5 — Normalization Engine  
**Estimated Effort:** Medium (3–5 days)

### Problem

The parser architecture is monolithic. Each `BaseParser` subclass (CSV, JSON, PDF, TXT) owns both format-specific reading logic and format-agnostic transformation logic in a single `parse()` method. This means:

- Every new tabular format (TSV, Excel, Google Sheets) requires a new parser class that duplicates column-mapping logic.
- The `CsvParser` silently drops all rows after the first; a general-purpose mapper should handle multi-row sources.
- Skill parsing (`_parse_skill_list`) and experience accumulation (`_accumulate_experience`) are private methods — not reusable by other parsers.
- Testing requires instantiating the full parser even for mapping-only changes.

### Solution

Split into two layers with a common record format as the seam:

```
Reader (format-specific)  →  Iterator[dict[str, str]]  →  CandidateMapper (format-agnostic)
```

| Component | Responsibility | Tests |
|---|---|---|
| `Reader` (ABC) | Parse raw bytes into row dicts; knows delimiters, sheets, API pagination | Unit per reader |
| `CandidateMapper` | Transform row dicts into `CanonicalCandidate`; owns column mapping, skill/experience handling, warnings | Pure unit |
| `CsvParser` (bridge) | `CsvReader.read(raw_data) → CandidateMapper.map_rows(rows)` | Integration only |

### Acceptance Criteria

- `CandidateMapper` is extracted from `CsvParser` private methods with zero behavioural change.
- `CsvReader` implements `Reader`; `CsvParser.parse()` delegates to both.
- `TSVReader` is implemented as a parameterized `CsvReader`.
- `PdfResumeParser` and `TxtNotesParser` remain monolithic (they are not tabular).
- All existing CSV parser tests pass without modification.
- Registry is updated to accept `Reader` classes alongside (or instead of) monolithic parsers for tabular formats.

---

## Item #2: Advanced Column Mapping Configuration

**Priority:** High  
**Target Phase:** Phase 5 — Normalization Engine  
**Estimated Effort:** Small (1–2 days)

### Problem

The current column mapping is a flat `dict[str, str]` mapping CSV header names to dotted field paths:

```python
DEFAULT_COLUMN_MAPPING = {
    "name": "name.display_name",
    "email": "contact.emails[0].value",
}
```

This lacks support for:
- **Required columns** — mapping cannot express "this column must exist; fail if missing".
- **Type coercion** — no way to specify `int`, `float`, or custom parser per column.
- **Default values** — cannot supply a default when a column is absent.
- **Transform functions** — cannot apply per-column normalisation (e.g., uppercase a name, strip country code from a phone).
- **Alternative names** — only the primary key is checked; there is no explicit alias mechanism (currently handled by adding duplicate mapping entries like `phone_number` and `mobile`, both pointing to the same field).

### Solution

Replace the flat string-valued mapping with a nested rule object:

```python
class ColumnRule(BaseModel):
    target: str
    required: bool = False
    default: str | None = None
    type: str = "str"                           # "str" | "int" | "float" | "email" | "phone"
    aliases: list[str] = []                     # Alternative header names
    transform: str | None = None                # Named transform function key
```

Example configuration:

```python
ADVANCED_COLUMN_MAPPING = {
    "Full Name": ColumnRule(
        target="name.display_name",
        required=True,
    ),
    "Email": ColumnRule(
        target="contact.emails[0].value",
        required=False,
        type="email",
    ),
    "Years Experience": ColumnRule(
        target="experience[0].years",
        required=False,
        type="int",
        default="0",
    ),
}
```

### Benefits

- **Self-documenting** — each column's constraints are explicit in the mapping.
- **Fail-fast validation** — `required=True` columns missing from input raise immediately, not with a warning.
- **Extensible** — new rule keys (`min_length`, `pattern`, `transform`) can be added without changing the mapper interface.
- **Backward compatible** — the mapper can accept both the old `dict[str, str]` and new `dict[str, ColumnRule]` formats with auto-detection.

### Migration Path

1. Add `ColumnRule` Pydantic model to `app/parsers/column_rule.py`.
2. Add a `_normalize_mapping()` helper to `CandidateMapper` that upcasts flat strings to `ColumnRule(target=value)`.
3. Add `type` and `required` enforcement to `CandidateMapper.map_row()`.
4. Update `DEFAULT_COLUMN_MAPPING` to use `ColumnRule` objects (backward-compatible).
5. Add `transform` registry for reusable per-column normalisation functions.
