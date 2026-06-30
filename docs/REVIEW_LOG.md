# Review Log

Records of completed review cycles, design improvements, and feedback loops for each phase.

---

## Phase 1 Review — Project Setup
**Status:** Approved

Changes requested/implemented:
- Initialize Python project with `pyproject.toml`
- Configure `ruff`, `mypy`, `pytest`
- Set up project directory structure
- Define dependencies (FastAPI, Pydantic, python-multipart, google-genai, PyMuPDF, python-dotenv)

---

## Phase 2 Review — Canonical Model
**Status:** Approved

Changes requested/implemented:
- Define `CanonicalCandidate` as aggregate root
- Define `PersonName`, `ContactInformation`, `Phone`, `Email`, `Location`, `PartialDate` value objects
- Define `Skill`, `Experience`, `Education`, `Certification`, `Project`, `Organization` entities
- Define `Provenance`, `Confidence`, `Warning`, `ProcessingMetadata` metadata models
- Define `SourceType` enum with `StrEnum`
- Define `Provenanced[T]` generic wrapper for field-level provenance

---

## Phase 3 Review — Parser Factory
**Status:** Approved

Changes requested/implemented:
- Define `BaseParser` abstract class with `parse()` contract
- Implement `ParserRegistry` with `freeze()` mechanism
- Implement `ParserFactory` with automatic `AiClient` DI via `inspect.signature`
- Register parsers via `default_registry` at app startup

---

## Phase 4 Review — CSV Parser
**Status:** Approved

Changes requested/implemented:
- Implement `CsvParser` with `csv.DictReader`
- Default column mapping with case-insensitive header matching
- `DEFAULT_COLUMN_MAPPING` maps common CSV headers to canonical fields
- Multiple skill delimiters (`|`, `;`, `,`)
- Missing/empty value handling
- Unknown column warnings
- 31 passing tests covering happy path, edge cases, skills, warnings, mapping

Future improvements noted:
- Reader / Mapper split (Phase 5)
- Advanced column mapping with `ColumnRule` (Tech Debt Item #2)
- Multi-row CSV support

---

## Phase 5 Review — Reader / Mapper Architecture
**Status:** Approved

Changes requested/implemented:
- Extract `CSVReader` from CsvParser — handles encoding, BOM, delimiter, produces `CSVRecord` objects
- Create `CSVRecord` frozen dataclass (row_number, headers, values) as the seam between Reader and Mapper
- Extract `CandidateMapper` from CsvParser — configurable column mapping, warnings, nested field setting
- Refactor `CsvParser` to a thin orchestrator: `CSVReader.read()` → `CandidateMapper.map()` → candidate
- Fix latent bug: whitespace-padded headers no longer generate false `UNKNOWN_COLUMN` warnings
- Add 30 new unit tests (11 CSVReader + 19 CandidateMapper) testing each component in isolation
- All 64 tests pass, lint clean, mypy clean
- `CSVReader` is reusable for TSV via `CSVReader(delimiter="\t")`
