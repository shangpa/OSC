from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import tomllib
from tomllib import TOMLDecodeError
from typing import Any

from .scan import IGNORED_DIRS

MCP_REF = re.compile(r"mcp(?:\s+server)?\s*[:=]\s*([A-Za-z0-9_.-]+)", re.IGNORECASE)
SERVER_TABLE = re.compile(r"^\s*\[(?:mcp_servers|mcpServers)\.([^\]]+)\]", re.MULTILINE)
BROAD_PATHS = {"/", "/*", "/mnt", "/mnt/c", "C:\\", "C:/", "~"}
MAX_TOML_BYTES = 1024 * 1024


@dataclass(frozen=True)
class McpFinding:
    status: str
    code: str
    message: str


@dataclass(frozen=True)
class McpDoctorReport:
    config_path: Path | None
    server_names: list[str]
    referenced_servers: list[str]
    findings: list[McpFinding]

    @property
    def status_counts(self) -> dict[str, int]:
        counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
        for finding in self.findings:
            counts[finding.status] = counts.get(finding.status, 0) + 1
        return counts


def discover_config(repo: str | Path) -> Path | None:
    root = Path(repo).resolve()
    project_config = root / ".codex" / "config.toml"
    if project_config.is_file():
        return project_config
    home = Path.home()
    user_config = home / ".codex" / "config.toml"
    if user_config.is_file():
        return user_config
    return None


def doctor_config(config_path: str | Path | None, repo: str | Path) -> McpDoctorReport:
    root = Path(repo).resolve()
    selected = Path(config_path).resolve() if config_path is not None else discover_config(root)
    referenced = _referenced_servers(root)
    findings: list[McpFinding] = []

    if selected is None:
        findings.append(McpFinding("WARN", "config-missing", "No MCP config found"))
        return McpDoctorReport(None, [], referenced, findings)
    if not selected.is_file():
        raise ValueError(f"MCP config not found: {selected}")

    if selected.stat().st_size > MAX_TOML_BYTES:
        raise ValueError(f"MCP config too large: {selected} exceeds {MAX_TOML_BYTES} bytes")
    config_text = selected.read_text(encoding="utf-8")
    duplicate_names = _duplicate_server_names(config_text)
    for name in duplicate_names:
        findings.append(McpFinding("WARN", "duplicate-server-name", f"duplicate MCP server name: {name}"))

    try:
        data = tomllib.loads(config_text)
        servers = _server_table(data)
        server_names = sorted(servers)
    except TOMLDecodeError:
        if not duplicate_names:
            raise
        servers = {}
        server_names = sorted(set(_server_table_names(config_text)))

    if server_names:
        findings.append(McpFinding("PASS", "servers-found", f"Configured MCP servers: {len(server_names)}"))
    else:
        findings.append(McpFinding("WARN", "servers-missing", "No MCP servers configured"))

    for name in server_names:
        if name not in servers:
            continue
        value = servers[name]
        if not isinstance(value, dict):
            findings.append(McpFinding("WARN", "server-invalid", f"{name} has invalid server config"))
            continue
        command = value.get("command")
        args = value.get("args")
        if not isinstance(command, str) or not command.strip():
            findings.append(McpFinding("WARN", "command-missing", f"{name} has missing command"))
        elif shutil.which(command) is None:
            findings.append(McpFinding("WARN", "command-binary-missing", f"{name} has missing command binary: {command}"))
        if not isinstance(args, list) or not args:
            findings.append(McpFinding("WARN", "args-missing", f"{name} has missing args"))
        elif any(_is_broad_access(arg) for arg in args if isinstance(arg, str)):
            findings.append(McpFinding("WARN", "broad-filesystem-access", f"{name} requests broad filesystem access"))

    configured = set(server_names)
    for name in referenced:
        if name not in configured:
            findings.append(McpFinding("WARN", "referenced-not-configured", f"MCP server {name} referenced but not configured"))

    return McpDoctorReport(selected, server_names, referenced, findings)


def render_mcp_report(report: McpDoctorReport) -> str:
    lines = [
        "# MCP Doctor",
        f"Config: {report.config_path if report.config_path is not None else 'not found'}",
        f"Configured servers: {len(report.server_names)}",
        f"Referenced servers: {len(report.referenced_servers)}",
        "",
    ]
    if report.server_names:
        lines.append("Servers:")
        for name in report.server_names:
            lines.append(f"- {name}")
        lines.append("")

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


def _server_table(data: dict[str, Any]) -> dict[str, Any]:
    value = data.get("mcp_servers", data.get("mcpServers", {}))
    if not isinstance(value, dict):
        raise ValueError("mcp_servers must be a table/object")
    return value


def _referenced_servers(root: Path) -> list[str]:
    refs: set[str] = set()
    for path in _reference_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        refs.update(match.group(1) for match in MCP_REF.finditer(text))
    return sorted(refs)


def _reference_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("AGENTS.md"):
        if _is_ignored(path):
            continue
        files.append(path)
    for path in root.rglob("*.md"):
        if _is_ignored(path):
            continue
        parts = set(path.parts)
        if path.name == "SKILL.md" or "skills" in parts:
            files.append(path)
    return sorted(set(files))


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def _server_table_names(text: str) -> list[str]:
    return [match.group(1).strip().strip('"') for match in SERVER_TABLE.finditer(text)]


def _duplicate_server_names(text: str) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for name in _server_table_names(text):
        if name in seen:
            duplicates.add(name)
        seen.add(name)
    return sorted(duplicates)


def _is_broad_access(value: str) -> bool:
    normalized = value.strip()
    return normalized in BROAD_PATHS
