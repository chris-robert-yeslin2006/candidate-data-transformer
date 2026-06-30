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

def main():
    parser = argparse.ArgumentParser(description="Run Candidate Data Transformer on custom inputs.")
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
        with open(args.projection, "r") as f:
            proj_config = json.load(f)
            
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
    
    # Output result
    print("\n=== Result ===")
    print(json.dumps(result.to_dict(), indent=2))

if __name__ == "__main__":
    main()
