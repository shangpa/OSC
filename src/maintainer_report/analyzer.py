from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MaintainerItem:
    kind: str
    number: int
    title: str
    state: str
    labels: tuple[str, ...]
    updated_at: date | None
    url: str


@dataclass(frozen=True)
class MaintainerReport:
    total_items: int
    open_issues: int
    open_pull_requests: int
    closed_items: int
    stale_open_items: tuple[MaintainerItem, ...]
    unlabeled_open_items: tuple[MaintainerItem, ...]
    label_counts: dict[str, int]


def load_export(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_items(raw: Any) -> list[MaintainerItem]:
    if isinstance(raw, list):
        return [_normalize_item(item, _infer_kind(item)) for item in raw]

    if not isinstance(raw, dict):
        raise ValueError("export must be a list or an object with issues, pull_requests, or items")

    normalized: list[MaintainerItem] = []
    found_bucket = False

    if "issues" in raw:
        found_bucket = True
        normalized.extend(_normalize_item(item, "issue") for item in _require_list(raw["issues"], "issues"))

    if "pull_requests" in raw:
        found_bucket = True
        normalized.extend(
            _normalize_item(item, "pull_request") for item in _require_list(raw["pull_requests"], "pull_requests")
        )

    if "items" in raw:
        found_bucket = True
        normalized.extend(_normalize_item(item, _infer_kind(item)) for item in _require_list(raw["items"], "items"))

    if not found_bucket:
        raise ValueError("export must be a list or an object with issues, pull_requests, or items")

    return normalized


def analyze_items(items: list[MaintainerItem], *, as_of: date, stale_days: int) -> MaintainerReport:
    open_items = [item for item in items if item.state == "open"]
    stale_open_items = tuple(
        item
        for item in open_items
        if item.updated_at is not None and (as_of - item.updated_at).days >= stale_days
    )
    unlabeled_open_items = tuple(item for item in open_items if not item.labels)
    label_counts = dict(sorted(Counter(label for item in items for label in item.labels).items()))

    return MaintainerReport(
        total_items=len(items),
        open_issues=sum(1 for item in open_items if item.kind == "issue"),
        open_pull_requests=sum(1 for item in open_items if item.kind == "pull_request"),
        closed_items=sum(1 for item in items if item.state == "closed"),
        stale_open_items=stale_open_items,
        unlabeled_open_items=unlabeled_open_items,
        label_counts=label_counts,
    )


def render_markdown(report: MaintainerReport) -> str:
    lines = [
        "# Maintainer Report",
        "",
        "## Summary",
        f"- Total items: {report.total_items}",
        f"- Open issues: {report.open_issues}",
        f"- Open pull requests: {report.open_pull_requests}",
        f"- Closed items: {report.closed_items}",
        f"- Stale open items: {len(report.stale_open_items)}",
        f"- Unlabeled open items: {len(report.unlabeled_open_items)}",
        "",
        "## Attention Queue",
    ]

    attention_items = _attention_items(report)
    if attention_items:
        for item, reasons in attention_items:
            label_text = ", ".join(item.labels) if item.labels else "none"
            url_text = f" - {item.url}" if item.url else ""
            lines.append(f"- {item.kind} #{item.number} {item.title} [{', '.join(reasons)}] - labels: {label_text}{url_text}")
    else:
        lines.append("- No open items require attention based on this export.")

    lines.extend(["", "## Stale Open Items"])
    if report.stale_open_items:
        for item in report.stale_open_items:
            lines.append(f"- {item.kind} #{item.number} {item.title}")
    else:
        lines.append("- None")

    lines.extend(["", "## Unlabeled Open Items"])
    if report.unlabeled_open_items:
        for item in report.unlabeled_open_items:
            lines.append(f"- {item.kind} #{item.number} {item.title}")
    else:
        lines.append("- None")

    lines.extend(["", "## Label Frequency"])
    if report.label_counts:
        for label, count in report.label_counts.items():
            lines.append(f"- {label}: {count}")
    else:
        lines.append("- No labels found")

    return "\n".join(lines) + "\n"


def _attention_items(report: MaintainerReport) -> list[tuple[MaintainerItem, list[str]]]:
    stale_numbers = {(item.kind, item.number) for item in report.stale_open_items}
    unlabeled_numbers = {(item.kind, item.number) for item in report.unlabeled_open_items}
    items = {
        (item.kind, item.number): item
        for item in (*report.stale_open_items, *report.unlabeled_open_items)
    }

    result: list[tuple[MaintainerItem, list[str]]] = []
    for key in sorted(items, key=lambda value: (value[0] != "issue", value[1])):
        reasons: list[str] = []
        if key in stale_numbers:
            reasons.append("stale")
        if key in unlabeled_numbers:
            reasons.append("unlabeled")
        result.append((items[key], reasons))
    return result


def _normalize_item(raw_item: Any, kind: str) -> MaintainerItem:
    if not isinstance(raw_item, dict):
        raise ValueError("export items must be objects")

    return MaintainerItem(
        kind=kind,
        number=int(raw_item.get("number", raw_item.get("id", 0))),
        title=str(raw_item.get("title", "Untitled")),
        state=str(raw_item.get("state", "open")).lower(),
        labels=_normalize_labels(raw_item.get("labels", [])),
        updated_at=_parse_date(raw_item.get("updated_at") or raw_item.get("created_at")),
        url=str(raw_item.get("html_url", raw_item.get("url", ""))),
    )


def _infer_kind(raw_item: Any) -> str:
    if not isinstance(raw_item, dict):
        raise ValueError("export items must be objects")
    if raw_item.get("kind") in {"issue", "pull_request"}:
        return str(raw_item["kind"])
    if "pull_request" in raw_item:
        return "pull_request"
    url = str(raw_item.get("html_url", raw_item.get("url", "")))
    if "/pull/" in url or "/pulls/" in url:
        return "pull_request"
    return "issue"


def _normalize_labels(raw_labels: Any) -> tuple[str, ...]:
    if raw_labels is None:
        return ()
    if not isinstance(raw_labels, list):
        raise ValueError("labels must be a list")

    labels: list[str] = []
    for raw_label in raw_labels:
        if isinstance(raw_label, str):
            label = raw_label
        elif isinstance(raw_label, dict) and "name" in raw_label:
            label = str(raw_label["name"])
        else:
            raise ValueError("labels must be strings or objects with a name")
        if label:
            labels.append(label)
    return tuple(labels)


def _parse_date(raw_value: Any) -> date | None:
    if raw_value in (None, ""):
        return None
    if not isinstance(raw_value, str):
        raise ValueError("date values must be strings")
    value = raw_value.removesuffix("Z")
    return datetime.fromisoformat(value).date()


def _require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value
