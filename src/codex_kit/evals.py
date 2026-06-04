from __future__ import annotations

from pathlib import Path
import json
from typing import Any, TextIO

DEFAULT_CONFIG = Path(".codex-kit") / "evals.json"


def init_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = {"version": 1, "cases": []}
    _save_config(config_path, config)
    return config


def load_config(path: str | Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.is_file():
        raise ValueError(f"eval config not found: {config_path}")
    data = json.loads(config_path.read_text(encoding="utf-8"))
    _validate_config(data)
    return data


def add_case(
    path: str | Path,
    *,
    name: str,
    prompt: str,
    expected_command: str,
    allowed_changes: str,
) -> dict[str, Any]:
    config_path = Path(path)
    config = load_config(config_path)
    if any(case["name"] == name for case in config["cases"]):
        raise ValueError(f"eval case already exists: {name}")
    config["cases"].append(
        {
            "name": name,
            "prompt": prompt,
            "expected_command": expected_command,
            "allowed_changes": allowed_changes,
        }
    )
    _save_config(config_path, config)
    return config


def render_dry_run(config: dict[str, Any]) -> str:
    lines = ["# Codex Kit Eval DRY RUN", f"Task count: {len(config['cases'])}", ""]
    if not config["cases"]:
        lines.append("- No eval cases registered")
    for case in config["cases"]:
        lines.extend(
            [
                f"## {case['name']}",
                f"Prompt: {case['prompt']}",
                f"Expected verification command: {case['expected_command']}",
                f"Allowed changed files: {case['allowed_changes']}",
                "Agent execution: disabled in dry-run",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_report(config: dict[str, Any]) -> str:
    invalid = [case for case in config["cases"] if not all(case.get(field) for field in _case_fields())]
    lines = [
        "# Eval Report",
        f"Version: {config['version']}",
        f"Task count: {len(config['cases'])}",
        f"Validation: {'PASS' if not invalid else 'FAIL'}",
    ]
    if config["cases"]:
        lines.append("")
        for case in config["cases"]:
            lines.append(f"- {case['name']}: {case['expected_command']} ({case['allowed_changes']})")
    return "\n".join(lines) + "\n"


def write_init_result(stdout: TextIO, path: Path) -> int:
    init_config(path)
    stdout.write(f"Initialized eval config: {path}\n")
    return 0


def write_add_result(stdout: TextIO, path: Path, name: str, prompt: str, verify: str, allowed_changes: str) -> int:
    add_case(path, name=name, prompt=prompt, expected_command=verify, allowed_changes=allowed_changes)
    stdout.write(f"Added eval case: {name}\n")
    return 0


def _save_config(path: Path, config: dict[str, Any]) -> None:
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_config(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValueError("eval config must be an object")
    if data.get("version") != 1:
        raise ValueError("eval config version must be 1")
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise ValueError("eval config cases must be a list")
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("eval cases must be objects")
        for field in _case_fields():
            if not isinstance(case.get(field), str) or not case[field].strip():
                raise ValueError(f"eval case missing field: {field}")


def _case_fields() -> tuple[str, ...]:
    return ("name", "prompt", "expected_command", "allowed_changes")
