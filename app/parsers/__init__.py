"""
Source-specific parsers and parser framework.

Provides the BaseParser abstract interface, concrete parser
implementations for each supported source format, and the
ParserRegistry / ParserFactory plugin architecture.

Adding a new parser:
    1. Create a new class inheriting from BaseParser
    2. Define ``source_type`` class attribute
    3. Register it with the default registry

The default_registry is pre-populated with all built-in parsers
and frozen after registration to prevent runtime changes.

Future:
    Plugin packages will register additional parsers before the
    registry is frozen. External parser modules can be loaded
    via entry points or a discovery mechanism and registered
    via ``default_registry.register()``.

Reader / Mapper Architecture (Phase 5):
    Tabular formats are now handled by two separate layers:
    - Readers (CSVReader, TSVReader) handle format-specific I/O
    - CandidateMapper handles format-agnostic field mapping
    See csv_reader.py, csv_record.py, and candidate_mapper.py.
"""

from app.parsers.ats_json_parser import AtsJsonParser
from app.parsers.base import BaseParser
from app.parsers.candidate_mapper import CandidateMapper
from app.parsers.csv_parser import CsvParser
from app.parsers.csv_reader import CSVReader
from app.parsers.csv_record import CSVRecord
from app.parsers.pdf_parser import PdfResumeParser
from app.parsers.registry import ParserFactory, ParserRegistry
from app.parsers.txt_parser import TxtNotesParser

# Default registry pre-populated with all built-in parsers.
default_registry = ParserRegistry()
default_registry.register(CsvParser)
default_registry.register(PdfResumeParser)
default_registry.register(TxtNotesParser)
default_registry.register(AtsJsonParser)

# Freeze the registry after initialization to prevent
# accidental runtime reconfiguration.
default_registry.freeze()

__all__ = [
    "AtsJsonParser",
    "BaseParser",
    "CandidateMapper",
    "CSVReader",
    "CSVRecord",
    "CsvParser",
    "ParserFactory",
    "ParserRegistry",
    "PdfResumeParser",
    "TxtNotesParser",
    "default_registry",
]
