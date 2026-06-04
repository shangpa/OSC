from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

IGNORED_DIRS = {".git", ".omo", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv", "dist", "build"}
COMMAND_HINTS = ("test", "build", "lint", "pytest", "unittest", "compileall", "npm test", "pnpm test")
UNSAFE_PATTERNS = (
    "git reset --hard",
    "git clean -fd",
    "git clean -xdf",
    "git push --force",
    "git push -f",
    "rm -rf",
)
PATH_TOKEN = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class Finding:
    status: str
    code: str
    message: str


@dataclass(frozen=True)
class ScanReport:
    root: Path
    agents_files: list[str]
    codex_config_present: bool
    mcp_reference_count: int
    findings: list[Finding]

    @property
    def status_counts(self) -> dict[str, int]:
        counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
        for finding in self.findings:
            counts[finding.status] = counts.get(finding.status, 0) + 1
        return counts


def scan_repository(root: str | Path) -> ScanReport:
    repo = Path(root).resolve()
    if not repo.exists() or not repo.is_dir():
        raise ValueError(f"repository path does not exist or is not a directory: {root}")

    agents_files = sorted(_relative(path, repo) for path in _walk_files(repo, "AGENTS.md"))
    codex_config_present = (repo / ".codex" / "config.toml").is_file()
    findings: list[Finding] = []

    if agents_files:
        findings.append(Finding("PASS", "agents-found", f"AGENTS.md files: {len(agents_files)}"))
    else:
        findings.append(Finding("FAIL", "agents-missing", "No AGENTS.md files found"))

    if codex_config_present:
        findings.append(Finding("PASS", "codex-config-found", ".codex/config.toml found"))
    else:
        findings.append(Finding("WARN", "codex-config-missing", ".codex/config.toml not found"))

    mcp_references = 0
    for relative in agents_files:
        path = repo / relative
        text = path.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        if "mcp" in lower:
            mcp_references += lower.count("mcp")
        findings.extend(_agent_findings(path, relative, text, repo))

    if codex_config_present:
        config_text = (repo / ".codex" / "config.toml").read_text(encoding="utf-8", errors="replace")
        if "mcp" in config_text.lower():
            mcp_references += config_text.lower().count("mcp")

    if mcp_references:
        findings.append(Finding("PASS", "mcp-references", f"MCP references found: {mcp_references}"))
    else:
        findings.append(Finding("WARN", "mcp-references-missing", "No likely MCP references found"))

    if (repo / "package.json").is_file() and (repo / "node_modules").exists():
        findings.append(
            Finding(
                "WARN",
                "windows-wsl-node-modules",
                "node_modules is present beside package.json; avoid sharing native dependencies across Windows/WSL",
            )
        )

    return ScanReport(repo, agents_files, codex_config_present, mcp_references, findings)


def render_scan_report(report: ScanReport) -> str:
    lines = [
        "# Codex Kit Scan",
        f"Repository: {report.root}",
        f"AGENTS.md files: {len(report.agents_files)}",
        f".codex/config.toml: {'present' if report.codex_config_present else 'missing'}",
        "",
    ]
    by_status = {"PASS": [], "WARN": [], "FAIL": []}
    for finding in report.findings:
        by_status.setdefault(finding.status, []).append(finding)

    for status in ("PASS", "WARN", "FAIL"):
        lines.append(f"## {status} ({len(by_status[status])})")
        if by_status[status]:
            for finding in by_status[status]:
                lines.append(f"- [{finding.code}] {finding.message}")
        else:
            lines.append("- None")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _agent_findings(path: Path, relative: str, text: str, repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    line_count = text.count("\n") + 1
    if len(text) > 12000 or line_count > 250:
        findings.append(Finding("WARN", "agents-too-large", f"{relative} is overly large ({line_count} lines)"))

    lower = text.lower()
    if not any(hint in lower for hint in COMMAND_HINTS):
        findings.append(Finding("WARN", "commands-missing", f"{relative} has missing test/build command hints"))

    for pattern in UNSAFE_PATTERNS:
        if pattern in lower:
            findings.append(Finding("FAIL", "unsafe-instruction", f"{relative} contains unsafe destructive instruction: {pattern}"))
            break

    for token in _path_tokens(text):
        candidate = (path.parent / token).resolve() if not token.startswith(('/', '~')) else Path(token)
        if _looks_like_path(token) and not candidate.exists():
            findings.append(Finding("WARN", "stale-path", f"{relative} references stale path: {token}"))

    return findings


def _path_tokens(text: str) -> list[str]:
    return [match.group(1).strip() for match in PATH_TOKEN.finditer(text)]


def _looks_like_path(token: str) -> bool:
    if token.startswith("-") or " " in token or token.startswith("git ") or token.startswith("python "):
        return False
    return "/" in token or "\\" in token or bool(Path(token).suffix)


def _walk_files(root: Path, filename: str) -> list[Path]:
    matches: list[Path] = []
    for path in root.rglob(filename):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file():
            matches.append(path)
    return matches


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()
