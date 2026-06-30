"""
Interactive CLI demo for the Candidate Data Transformer pipeline.

Walks through the full transformation flow step-by-step:
  1. Pick sample source files (CSV, JSON, TXT)
  2. Run the pipeline → show canonical merged output
  3. Optionally pick a company-specific projection template
  4. Show the projected output in that company's format

Usage:
    python scripts/demo_cli.py [--confidence] [-c]

Options:
    --confidence, -c    Show detailed confidence score breakdown
                        (field-level scores, factors, etc.)
"""

import argparse
import json
import os
import sys

# Force UTF-8 output on Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.parsers import default_registry
from app.parsers.registry import ParserFactory
from app.services.pipeline_service import PipelineService
from app.domain.models.provenance import SourceType

# ── Styling helpers ──────────────────────────────────────────────────

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

DIVIDER = f"{DIM}{'-' * 60}{RESET}"
DIVIDER_THICK = f"{CYAN}{'=' * 60}{RESET}"


def banner():
    print()
    print(DIVIDER_THICK)
    print(f"{BOLD}{CYAN}   *  Candidate Data Transformer  -  Interactive Demo{RESET}")
    print(DIVIDER_THICK)
    print()


def heading(text: str):
    print()
    print(f"  {BOLD}{MAGENTA}> {text}{RESET}")
    print(f"  {DIM}{'-' * (len(text) + 2)}{RESET}")


def info(text: str):
    print(f"  {DIM}{text}{RESET}")


def success(text: str):
    print(f"  {GREEN}[OK] {text}{RESET}")


def warn(text: str):
    print(f"  {YELLOW}[!] {text}{RESET}")


def error(text: str):
    print(f"  {RED}[X] {text}{RESET}")


def pretty_json(data, indent=4):
    """Return coloured JSON string for terminal display."""
    return json.dumps(data, indent=indent, default=str)


# ── Discovery helpers ────────────────────────────────────────────────

SAMPLES_DIR = os.path.join(PROJECT_ROOT, "samples")
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")

EXT_TO_SOURCE_TYPE = {
    "csv": SourceType.CSV,
    "tsv": SourceType.CSV,
    "json": SourceType.ATS_JSON,
    "txt": SourceType.TXT_NOTES,
    "md": SourceType.TXT_NOTES,
    "pdf": SourceType.PDF_RESUME,
}

FORMAT_LABELS = {
    SourceType.CSV: "CSV (Structured table)",
    SourceType.ATS_JSON: "ATS JSON (Structured profile)",
    SourceType.TXT_NOTES: "Text Notes (Unstructured)",
    SourceType.PDF_RESUME: "PDF Resume (Unstructured)",
}


def discover_samples() -> list[dict]:
    """Return list of {path, name, source_type, label} for every sample file."""
    samples = []
    if not os.path.isdir(SAMPLES_DIR):
        return samples
    for fname in sorted(os.listdir(SAMPLES_DIR)):
        if fname.startswith("."):
            continue
        ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
        st = EXT_TO_SOURCE_TYPE.get(ext, SourceType.CSV)
        samples.append({
            "path": os.path.join(SAMPLES_DIR, fname),
            "name": fname,
            "source_type": st,
            "label": FORMAT_LABELS.get(st, str(st)),
        })
    return samples


def discover_templates() -> list[dict]:
    """Return list of {path, name, content} for every projection template."""
    templates = []
    if not os.path.isdir(CONFIG_DIR):
        return templates
    for fname in sorted(os.listdir(CONFIG_DIR)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(CONFIG_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = json.load(f)
            templates.append({
                "path": fpath,
                "name": fname.rsplit(".", 1)[0],
                "content": content,
            })
        except Exception:
            pass
    return templates


def read_file(path: str) -> str | bytes:
    """Read a file — binary for PDFs, text for everything else."""
    ext = path.rsplit(".", 1)[-1].lower()
    mode = "rb" if ext == "pdf" else "r"
    with open(path, mode, encoding=None if ext == "pdf" else "utf-8") as f:
        return f.read()


def prompt_choice(prompt: str, choices: list[str], allow_multiple: bool = False) -> list[int]:
    """
    Display numbered choices and return the selected indices.
    If allow_multiple, the user can type e.g. '1,3' or '1 3'.
    """
    for i, c in enumerate(choices, 1):
        print(f"    {CYAN}{i}{RESET}) {c}")
    print()

    while True:
        raw = input(f"  {BOLD}{prompt}{RESET} ").strip()
        if not raw:
            continue
        try:
            if allow_multiple:
                parts = raw.replace(",", " ").split()
                indices = [int(p) - 1 for p in parts]
            else:
                indices = [int(raw) - 1]

            if all(0 <= idx < len(choices) for idx in indices):
                return indices
        except ValueError:
            pass
        error(f"Invalid input. Enter number(s) between 1 and {len(choices)}.")


# ── Confidence display ───────────────────────────────────────────────

def show_confidence_details(result):
    """
    Display detailed confidence score breakdown.

    Extendable: add new score types by appending to the sections list.
    Each section is a (title, rows) pair where rows is a list of
    (label, value, color_fn) tuples.
    """
    confidence = result.confidence

    heading("Confidence Score Breakdown")

    sections = []

    # Section 1: Overall score
    overall_pct = confidence.overall * 100
    color = GREEN if confidence.overall >= 0.8 else (YELLOW if confidence.overall >= 0.5 else RED)
    overall_rows = [
        ("Overall Score", f"{overall_pct:.1f}%", color),
    ]
    sections.append(("Overall", overall_rows))

    # Section 2: Field-level scores
    if confidence.fields:
        field_rows = []
        for fname, fscore in sorted(confidence.fields.items()):
            fpct = fscore * 100
            fcolor = GREEN if fscore >= 0.8 else (YELLOW if fscore >= 0.5 else RED)
            field_rows.append((fname, f"{fpct:.1f}%", fcolor))
        sections.append(("Per-Field Scores", field_rows))

    # Section 3: Factors breakdown
    if confidence.factors:
        factor_rows = []
        for key, val in confidence.factors.items():
            factor_rows.append((key.replace("_", " ").title(), str(val), CYAN))
        sections.append(("Scoring Factors", factor_rows))

    # Render sections
    for title, rows in sections:
        print(f"  {BOLD}{title}{RESET}")
        for label, value, color in rows:
            bar_len = int(min(float(value.replace("%", "").replace("'", "")), 100) / 5) if "%" in value else 0
            bar = "#" * bar_len + "." * (20 - bar_len) if bar_len <= 20 else ""
            label_padded = label.ljust(22)
            print(f"    {label_padded}  {color}{value:>8}{RESET}  {DIM}{bar}{RESET}")
        print()

    # Section 4: Confidence metadata (provenance info)
    if hasattr(result, 'provenance') and result.provenance:
        prov_str = ", ".join(result.provenance)
        print(f"  {BOLD}Source Provenance{RESET}")
        print(f"    {'Sources:'.ljust(22)}  {DIM}{prov_str}{RESET}")
        print()


# ── Main flow ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Interactive CLI demo for Candidate Data Transformer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/demo_cli.py
  python scripts/demo_cli.py --confidence
  python scripts/demo_cli.py -c
        """,
    )
    parser.add_argument(
        "--confidence", "-c",
        action="store_true",
        default=False,
        help="Show detailed confidence score breakdown (field-level scores, factors, etc.)",
    )
    args = parser.parse_args()
    show_conf = args.confidence

    banner()

    # ─── Step 1: discover and show sample files ──────────────────────
    samples = discover_samples()
    if not samples:
        error("No sample files found in samples/ directory.")
        sys.exit(1)

    heading("Step 1 — Select sample source files to transform")
    info("These are the sample data files available in your codebase:")
    print()

    choice_labels = []
    for s in samples:
        choice_labels.append(f"{s['name']}  {DIM}({s['label']}){RESET}")

    selected_indices = prompt_choice(
        "Pick files to transform (comma-separated, e.g. 1,2): ",
        choice_labels,
        allow_multiple=True,
    )

    selected_samples = [samples[i] for i in selected_indices]
    print()
    for s in selected_samples:
        success(f"Selected: {s['name']}  →  {s['source_type']}")

    # ─── Step 2: show file contents ──────────────────────────────────
    heading("Step 2 — Previewing selected source data")
    for s in selected_samples:
        print()
        print(f"  {BOLD}{s['name']}{RESET}  {DIM}({s['label']}){RESET}")
        print(DIVIDER)
        content = read_file(s["path"])
        if isinstance(content, bytes):
            info(f"[Binary file — {len(content)} bytes]")
        else:
            # Show first ~15 lines
            lines = content.splitlines()
            for line in lines[:15]:
                print(f"  {DIM}|{RESET} {line}")
            if len(lines) > 15:
                info(f"  ... ({len(lines) - 15} more lines)")
        print(DIVIDER)

    # ─── Step 3: run pipeline (default projection) ───────────────────
    heading("Step 3 — Running transformation pipeline")
    info("parse -> normalize -> merge -> confidence -> project -> validate")
    print()

    parser_factory = ParserFactory(registry=default_registry, default_ai_client=None)
    pipeline = PipelineService(parser_factory=parser_factory)

    file_descriptors = []
    for s in selected_samples:
        raw = read_file(s["path"])
        file_descriptors.append({
            "raw_data": raw,
            "source_type": s["source_type"],
            "source_id": s["name"],
        })

    result = pipeline.process(files=file_descriptors)

    success(f"Pipeline completed in {result.processing_duration:.4f}s")
    success(f"Valid: {result.is_valid}")
    # noinspection PyUnresolvedReferences
    success(f"Overall confidence: {result.confidence.overall:.0%}")
    success(f"Sources merged: {', '.join(result.provenance)}")

    # Show detailed confidence breakdown if requested
    if show_conf:
        show_confidence_details(result)

    if result.warnings:
        print()
        for w in result.warnings:
            warn(f"[{w.code}] {w.message}  (field: {w.field or '-'})")

    # Show canonical merged output (default projection)
    heading("Step 4 — Canonical merged output (default projection)")
    info("This is the merged candidate data using the default field mapping:")
    print()
    print(f"{GREEN}{pretty_json(result.data)}{RESET}")

    # ─── Step 5: optional company-specific projection ────────────────
    heading("Step 5 — Company-specific projection (optional)")
    templates = discover_templates()

    if not templates:
        info("No projection templates found in config/ directory.")
        print()
        return

    info("Want to see what the output looks like for a specific company?")
    info("Available projection templates:")
    print()

    template_labels = []
    for t in templates:
        fields_preview = ", ".join(t["content"].get("fields", {}).keys())
        template_labels.append(
            f"{BOLD}{t['name']}{RESET}  {DIM}-> fields: [{fields_preview}]{RESET}"
        )
    template_labels.append(f"{DIM}Skip — no projection{RESET}")

    chosen = prompt_choice(
        "Pick a template (or skip): ",
        template_labels,
        allow_multiple=False,
    )
    chosen_idx = chosen[0]

    if chosen_idx >= len(templates):
        info("Skipping company projection. Done!")
        print()
        return

    template = templates[chosen_idx]

    # Show the template config
    heading(f"Template: {template['name']}")
    info(f"Config file: config/{template['name']}.json")
    print()
    print(f"{CYAN}{pretty_json(template['content'])}{RESET}")

    # Re-run pipeline with this projection
    heading(f"Step 6 — Projected output for '{template['name']}'")
    info("Re-running pipeline with company-specific field mapping...")
    print()

    result_proj = pipeline.process(
        files=file_descriptors,
        projection_config=template["content"],
    )

    print(f"{GREEN}{pretty_json(result_proj.data)}{RESET}")
    print()

    if show_conf:
        show_confidence_details(result_proj)

    success(f"Done! Confidence: {result_proj.confidence.overall:.0%}  |  "
            f"Valid: {result_proj.is_valid}  |  "
            f"Duration: {result_proj.processing_duration:.4f}s")

    # ─── Wrap-up ─────────────────────────────────────────────────────
    print()
    print(DIVIDER_THICK)
    print(f"  {BOLD}{GREEN}Demo complete!{RESET}  "
          f"Try the API: {CYAN}uvicorn app.main:app --reload{RESET}")
    print(DIVIDER_THICK)
    print()


if __name__ == "__main__":
    main()
