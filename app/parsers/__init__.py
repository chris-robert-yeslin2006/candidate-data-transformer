"""Source-specific parsers that produce canonical candidate models."""

from app.parsers.ats_json_parser import AtsJsonParser
from app.parsers.base import BaseParser
from app.parsers.csv_parser import CsvParser
from app.parsers.pdf_parser import PdfResumeParser
from app.parsers.txt_parser import TxtNotesParser

__all__ = [
    "BaseParser",
    "CsvParser",
    "PdfResumeParser",
    "TxtNotesParser",
    "AtsJsonParser",
]
