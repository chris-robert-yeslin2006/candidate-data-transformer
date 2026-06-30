# Title: ADR-005 — Reader / Mapper Architecture

## Decision
Split tabular format parsing into two independent layers: a **Reader** (format-specific I/O) and a **CandidateMapper** (format-agnostic transformation), joined by an immutable `CSVRecord` dataclass as the data seam.

## Why
- The original `CsvParser` violated single responsibility — one class handled encoding, BOM stripping, delimiter parsing, column matching, field assignment, skill parsing, warning generation, and provenance attachment.
- Every new tabular format (TSV, Excel, Google Sheets) would require duplicating column-mapping and field-assignment logic.
- Skill parsing (`_parse_skill_list`) and experience accumulation (`_accumulate_experience`) were private methods on `CsvParser`, unreusable by other parsers.
- Testing mapping logic required instantiating a full parser with CSV content, even when only testing column transformations.

## Alternatives Considered
- **Keep monolithic parser with shared utility functions** — rejected: utility functions lack cohesion; no clear seam prevents format-specific concerns from leaking into mapping logic.
- **Single Parser base class with template method** — rejected: inheritance hierarchies are less composable than Reader/Mapper delegation.
- **Generic `TableParser` that auto-detects format** — rejected: format detection is a separate concern; violates single responsibility.

## Tradeoffs
- **Pro:** Adding TSV support is `CSVReader(delimiter="\t")` — zero mapping code duplication.
- **Pro:** Adding Excel support requires only an `ExcelReader` producing `CSVRecord` objects — the mapper is unchanged.
- **Pro:** CandidateMapper is tested in pure isolation with hand-built CSVRecord objects (19 tests); no CSV parsing needed.
- **Pro:** The concrete `CSVReader` revealed the seam correctly before abstracting — a formal `Reader` ABC will be added when a second reader exists (YAGNI avoidance).
- **Con:** Three files instead of one (`csv_reader.py`, `csv_record.py`, `candidate_mapper.py` + thin `csv_parser.py`).
- **Con:** Slight indirection: `CsvParser.parse()` → `CSVReader.read()` → `CandidateMapper.map()` (acceptable for the architectural gain).

## Future Impact
- `CandidateMapper` becomes the single place for all column-mapping logic across tabular formats.
- `CSVRecord` (`frozen=True`) ensures Reader output is safely shareable.
- The architecture is ready for `TSVReader(delimiter="\t")`, `ExcelReader`, and `GoogleSheetsReader` without modifying mapping code.
- A formal `Reader` ABC with `read(raw_data) -> list[CSVRecord]` contract should be introduced when a second Reader implementation exists.
- Advanced column mapping with `ColumnRule` (Tech Debt Item #2) will be implemented on `CandidateMapper`, benefiting all tabular parsers.
