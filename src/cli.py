"""CLI entry point for AI Lease Parser."""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Optional

from .pdf_reader import read_file
from .extractor import extract, get_values
from .validator import validate
from .exporter import export


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Build and parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="ai-lease-parser",
        description="Extract structured data from residential lease PDFs.",
    )
    parser.add_argument(
        "input",
        help="Path to a lease PDF/TXT file or a folder containing multiple lease files.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="results.csv",
        help="Output file path (.csv or .xlsx). Default: results.csv",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        default=False,
        help="Use OpenAI LLM for higher-accuracy extraction (requires OPENAI_API_KEY).",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        default=False,
        help="Skip validation of extracted fields.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Suppress progress output.",
    )
    return parser.parse_args(argv)


def collect_files(input_path: str) -> List[Path]:
    """Collect all .pdf and .txt files from a file or directory."""
    p = Path(input_path)
    if p.is_file():
        return [p]
    elif p.is_dir():
        files = sorted(
            list(p.glob("*.pdf")) + list(p.glob("*.txt"))
        )
        return files
    else:
        raise FileNotFoundError(f"Input path not found: {input_path}")


def process_file(file_path: Path, use_llm: bool = False, quiet: bool = False) -> dict:
    """
    Process a single lease file and return extracted data dict.
    Includes a '_source' key with the filename.
    """
    if not quiet:
        print(f"  Processing: {file_path.name}")

    text = read_file(str(file_path))
    results = extract(text, use_llm=use_llm)
    values = get_values(results)
    values["_source"] = file_path.name
    return values


def run(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point. Returns exit code."""
    args = parse_args(argv)

    try:
        files = collect_files(args.input)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not files:
        print("No .pdf or .txt files found.", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"Found {len(files)} file(s) to process.")

    records = []
    all_valid = True

    for file_path in files:
        try:
            values = process_file(file_path, use_llm=args.use_llm, quiet=args.quiet)
        except Exception as e:
            print(f"  Warning: Failed to process {file_path.name}: {e}", file=sys.stderr)
            continue

        if not args.no_validate:
            validation = validate(values)
            if not validation["is_valid"]:
                all_valid = False
                if not args.quiet:
                    for err in validation["errors"]:
                        print(f"    Validation error in {file_path.name}: {err}")
            if validation["warnings"] and not args.quiet:
                for warn in validation["warnings"]:
                    print(f"    Warning in {file_path.name}: {warn}")

        records.append(values)

    if not records:
        print("No records extracted.", file=sys.stderr)
        return 1

    try:
        out_path = export(records, args.output)
        if not args.quiet:
            print(f"\nExported {len(records)} record(s) to: {out_path}")
    except Exception as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        return 1

    return 0 if all_valid else 2


def main():
    """Entry point for console_scripts."""
    sys.exit(run())


if __name__ == "__main__":
    main()
