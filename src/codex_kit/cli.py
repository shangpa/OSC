from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import TextIO

from .mcp import doctor_config, render_mcp_report
from .scan import render_scan_report, scan_repository


def main(argv: list[str] | None = None, *, stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
    output_stream = stdout if stdout is not None else sys.stdout
    error_stream = stderr if stderr is not None else sys.stderr
    parser = _build_parser()

    try:
        args = parser.parse_args(argv)
        if not hasattr(args, "handler"):
            parser.print_help(output_stream)
            return 0
        return args.handler(args, output_stream)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    except (OSError, ValueError) as exc:
        error_stream.write(f"error: {exc}\n")
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codex-kit", description="Repository-local utilities for Codex readiness.")
    subcommands = parser.add_subparsers(dest="command")

    scan = subcommands.add_parser("scan", help="Analyze a repository for Codex readiness")
    scan.add_argument("repository", nargs="?", default=".", type=Path, help="Repository path to scan (default: current directory)")
    scan.set_defaults(handler=_handle_scan)

    mcp = subcommands.add_parser("mcp", help="Inspect MCP configuration safety")
    mcp_subcommands = mcp.add_subparsers(dest="mcp_command")
    doctor = mcp_subcommands.add_parser("doctor", help="Validate MCP config without starting servers")
    doctor.add_argument("--config", type=Path, help="Path to Codex config TOML")
    doctor.add_argument("--repo", type=Path, default=Path("."), help="Repository path for AGENTS.md reference checks")
    doctor.set_defaults(handler=_handle_mcp_doctor)

    return parser


def _handle_scan(args: argparse.Namespace, stdout: TextIO) -> int:
    report = scan_repository(args.repository)
    stdout.write(render_scan_report(report))
    return 0


def _handle_mcp_doctor(args: argparse.Namespace, stdout: TextIO) -> int:
    report = doctor_config(args.config, args.repo)
    stdout.write(render_mcp_report(report))
    return 0
