from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys
from typing import TextIO

from .analyzer import analyze_items, load_export, normalize_items, render_markdown


def main(argv: list[str] | None = None, *, stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
    output_stream = stdout if stdout is not None else sys.stdout
    error_stream = stderr if stderr is not None else sys.stderr
    parser = _build_parser()

    try:
        args = parser.parse_args(argv)
        raw_export = load_export(args.input_json)
        items = normalize_items(raw_export)
        report = analyze_items(items, as_of=args.as_of, stale_days=args.stale_days)
        markdown = render_markdown(report)
        if args.output:
            args.output.write_text(markdown, encoding="utf-8")
        else:
            output_stream.write(markdown)
        return 0
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        error_stream.write(f"error: {exc}\n")
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maintainer-report",
        description="Turn issue and pull request export JSON into a maintainer triage report.",
    )
    parser.add_argument("input_json", type=Path, metavar="INPUT_JSON", help="Path to issue/PR export JSON")
    parser.add_argument(
        "--stale-days",
        type=_positive_int,
        default=30,
        help="Open items with no updates for this many days are marked stale (default: 30)",
    )
    parser.add_argument(
        "--as-of",
        type=_parse_date,
        default=date.today(),
        help="Date used for stale calculations in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument("--output", type=Path, help="Write markdown report to this path instead of stdout")
    return parser


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected YYYY-MM-DD") from exc


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed
