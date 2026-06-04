from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .scan import Finding, IGNORED_DIRS, scan_repository


@dataclass(frozen=True)
class AgentFile:
    path: str
    scope: str


def discover_agent_files(root: str | Path) -> list[AgentFile]:
    repo = Path(root).resolve()
    if not repo.exists() or not repo.is_dir():
        raise ValueError(f"repository path does not exist or is not a directory: {root}")

    files: list[AgentFile] = []
    for path in repo.rglob("AGENTS.md"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        relative = path.relative_to(repo).as_posix()
        parent = path.parent.relative_to(repo).as_posix()
        files.append(AgentFile(relative, "." if parent == "." else parent))
    return sorted(files, key=lambda item: (item.scope.count("/"), item.path))


def render_agents_graph(root: str | Path) -> str:
    files = discover_agent_files(root)
    lines = ["# AGENTS Graph", f"Repository: {Path(root).resolve()}", f"AGENTS.md files: {len(files)}", ""]
    if not files:
        lines.append("- No AGENTS.md files found")
        return "\n".join(lines) + "\n"

    lines.append("## Scope")
    for item in files:
        lines.append(f"- {item.path} -> applies to {item.scope}")

    lines.extend(["", "## Effective chain"] )
    for item in files:
        chain = [candidate.path for candidate in files if _scope_applies(candidate.scope, item.scope)]
        lines.append(f"- {item.scope}: " + " > ".join(chain))
    return "\n".join(lines) + "\n"


def render_agents_lint(root: str | Path) -> tuple[str, int]:
    report = scan_repository(root)
    findings = [finding for finding in report.findings if _is_agents_finding(finding)]
    if not findings and report.agents_files:
        findings = [Finding("PASS", "agents-clean", "AGENTS.md instructions passed lint checks")]

    lines = ["# AGENTS Lint", f"Repository: {report.root}", f"AGENTS.md files: {len(report.agents_files)}", ""]
    by_status = {"PASS": [], "WARN": [], "FAIL": []}
    for finding in findings:
        by_status[finding.status].append(finding)

    for status in ("PASS", "WARN", "FAIL"):
        lines.append(f"## {status} ({len(by_status[status])})")
        if by_status[status]:
            for finding in by_status[status]:
                lines.append(f"- [{finding.code}] {finding.message}")
        else:
            lines.append("- None")
        lines.append("")
    exit_code = 1 if by_status["FAIL"] else 0
    return "\n".join(lines).rstrip() + "\n", exit_code


def render_fix_dry_run(root: str | Path) -> str:
    report = scan_repository(root)
    lines = ["# Codex Kit Fix Dry Run", f"Repository: {report.root}", ""]
    suggestions: list[str] = []
    for finding in report.findings:
        if finding.code == "stale-path":
            suggestions.append(f"Would review stale path reference: {finding.message}")
        elif finding.code == "unsafe-instruction":
            suggestions.append(f"Would remove or rewrite unsafe instruction: {finding.message}")
        elif finding.code == "commands-missing":
            suggestions.append(f"Would add explicit test/build command hints: {finding.message}")
        elif finding.code == "agents-too-large":
            suggestions.append(f"Would split oversized AGENTS.md guidance: {finding.message}")
    if suggestions:
        lines.extend(f"- {suggestion}" for suggestion in suggestions)
    else:
        lines.append("- No safe automatic suggestions available")
    return "\n".join(lines) + "\n"


def _scope_applies(candidate: str, target: str) -> bool:
    return candidate == "." or target == candidate or target.startswith(candidate + "/")


def _is_agents_finding(finding: Finding) -> bool:
    return finding.code in {
        "agents-found",
        "agents-missing",
        "agents-too-large",
        "commands-missing",
        "unsafe-instruction",
        "stale-path",
    }
