"""
Script to run the Candidate Data Transformer pipeline directly from the command line.
Reads custom input files, executes the pipeline, and prints the normalized & merged output.
"""

import argparse
import json
import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parsers.registry import ParserFactory
from app.parsers import default_registry
from app.services.pipeline_service import PipelineService
from app.domain.models.provenance import SourceType

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def show_confidence_details(result):
    """Display detailed confidence score breakdown."""
    confidence = result.confidence

    print(f"\n  {BOLD}Confidence Score Breakdown{RESET}")
    print(f"  {'-' * 40}")

    # Overall score with bar
    overall_pct = confidence.overall * 100
    color = GREEN if confidence.overall >= 0.8 else (YELLOW if confidence.overall >= 0.5 else RED)
    bar_len = int(overall_pct / 5)
    bar = "#" * bar_len + "." * (20 - bar_len)
    print(f"    {'Overall:'.ljust(20)} {color}{overall_pct:>6.1f}%{RESET}  {DIM}{bar}{RESET}")

    # Field-level scores
    if confidence.fields:
        print()
        print(f"    {BOLD}Per-Field Scores:{RESET}")
        for fname, fscore in sorted(confidence.fields.items()):
            fpct = fscore * 100
            fcolor = GREEN if fscore >= 0.8 else (YELLOW if fscore >= 0.5 else RED)
            print(f"      {fname:<18} {fcolor}{fpct:>6.1f}%{RESET}")

    # Factors
    if confidence.factors:
        print()
        print(f"    {BOLD}Factors:{RESET}")
        for key, val in confidence.factors.items():
            print(f"      {key.replace('_', ' ').title():<20} {CYAN}{val}{RESET}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Run Candidate Data Transformer on custom inputs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_pipeline.py --files samples/sample_candidate.csv
  python scripts/run_pipeline.py --files samples/sample_notes.txt --confidence
  python scripts/run_pipeline.py --files samples/sample_candidate.json -c
  python scripts/run_pipeline.py --files samples/sample_candidate.csv --projection companyb
        """,
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Paths to input files to transform (CSV, JSON, TXT)."
    )
    parser.add_argument(
        "--projection",
        help="Path to custom projection configuration JSON file."
    )
    parser.add_argument(
        "--validation",
        help="Path to validation schema JSON file."
    )
    parser.add_argument(
        "--confidence", "-c",
        action="store_true",
        default=False,
        help="Show detailed confidence score breakdown (field-level scores, factors, etc.)",
    )
    
    args = parser.parse_args()
    
    # Setup pipeline
    parser_factory = ParserFactory(registry=default_registry, default_ai_client=None)
    pipeline = PipelineService(parser_factory=parser_factory)
    
    # Read files
    file_descriptors = []
    for file_path in args.files:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
            
        print(f"Loading {file_path}...")
        
        # Detect source type from file extension
        ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
        if ext == "csv":
            source_type = SourceType.CSV
            mode = "r"
        elif ext == "json":
            source_type = SourceType.ATS_JSON;
            mode = "r"
        elif ext == "pdf":
            source_type = SourceType.PDF_RESUME
            mode = "rb"
        elif ext in ["txt", "md"]:
            source_type = SourceType.TXT_NOTES
            mode = "r"
        else:
            print(f"Warning: Unknown extension '.{ext}', defaulting to CSV parsing.")
            source_type = SourceType.CSV
            mode = "r"
            
        with open(file_path, mode) as f:
            raw_data = f.read()
            
        file_descriptors.append({
            "raw_data": raw_data,
            "source_type": source_type,
            "source_id": os.path.basename(file_path)
        })
        
    # Load configs
    proj_config = None
    if args.projection:
        clean_name = args.projection.strip().lower()
        template_path = os.path.join("config", f"{clean_name}.json")
        if not clean_name.endswith(".json") and os.path.exists(template_path):
            print(f"Loading template from: {template_path}")
            with open(template_path, "r") as f:
                proj_config = json.load(f)
        elif os.path.exists(args.projection):
            with open(args.projection, "r") as f:
                proj_config = json.load(f)
        else:
            print(f"Error: Projection file or template not found: {args.projection}", file=sys.stderr)
            sys.exit(1)
            
    val_schema = None
    if args.validation:
        with open(args.validation, "r") as f:
            val_schema = json.load(f)
            
    print("\nRunning transformation pipeline...")
    result = pipeline.process(
        files=file_descriptors,
        projection_config=proj_config,
        validation_schema=val_schema
    )
    
    # Show confidence if requested
    if args.confidence:
        show_confidence_details(result)

    # Output result
    print("\n=== Result ===")
    print(json.dumps(result.to_dict(), indent=2))

if __name__ == "__main__":
    main()
