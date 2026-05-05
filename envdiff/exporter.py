"""Export EnvDiff results to various formats (JSON, CSV, Markdown)."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from typing import List, Literal

from envdiff.comparator import EnvDiff

ExportFormat = Literal["json", "csv", "markdown"]


@dataclass
class ExportOptions:
    fmt: ExportFormat = "json"
    show_values: bool = False


def _diff_to_rows(diff: EnvDiff, show_values: bool) -> List[dict]:
    rows: List[dict] = []
    for key in diff.missing_in_target:
        row = {"key": key, "status": "missing_in_target", "base": diff.base_name, "target": diff.target_name}
        if show_values:
            row["base_value"] = diff.base.get(key, "")
            row["target_value"] = ""
        rows.append(row)
    for key in diff.missing_in_base:
        row = {"key": key, "status": "missing_in_base", "base": diff.base_name, "target": diff.target_name}
        if show_values:
            row["base_value"] = ""
            row["target_value"] = diff.target.get(key, "")
        rows.append(row)
    for key, (bv, tv) in diff.mismatched.items():
        row = {"key": key, "status": "mismatch", "base": diff.base_name, "target": diff.target_name}
        if show_values:
            row["base_value"] = bv
            row["target_value"] = tv
        rows.append(row)
    return rows


def export_diff(diff: EnvDiff, options: ExportOptions | None = None) -> str:
    """Serialize a single EnvDiff to the requested format."""
    opts = options or ExportOptions()
    rows = _diff_to_rows(diff, opts.show_values)
    return _render(rows, opts.fmt)


def export_many(diffs: List[EnvDiff], options: ExportOptions | None = None) -> str:
    """Serialize multiple EnvDiff objects to the requested format."""
    opts = options or ExportOptions()
    rows: List[dict] = []
    for diff in diffs:
        rows.extend(_diff_to_rows(diff, opts.show_values))
    return _render(rows, opts.fmt)


def _render(rows: List[dict], fmt: ExportFormat) -> str:
    if fmt == "json":
        return json.dumps(rows, indent=2)
    if fmt == "csv":
        return _to_csv(rows)
    if fmt == "markdown":
        return _to_markdown(rows)
    raise ValueError(f"Unsupported export format: {fmt}")


def _to_csv(rows: List[dict]) -> str:
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def _to_markdown(rows: List[dict]) -> str:
    if not rows:
        return "_No differences found._\n"
    headers = list(rows[0].keys())
    lines = ["| " + " | ".join(headers) + " |",
             "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
    return "\n".join(lines) + "\n"
