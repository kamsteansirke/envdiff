"""Annotate .env files with inline comments describing schema rules and lint status."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file
from envdiff.schema import EnvSchema
from envdiff.linter import lint_env


@dataclass
class AnnotatedLine:
    """A single line from an .env file, optionally decorated with a note."""

    raw: str
    key: Optional[str] = None
    note: Optional[str] = None

    def render(self) -> str:
        if self.note:
            return f"{self.raw}  # [{self.note}]"
        return self.raw


@dataclass
class AnnotationResult:
    """Collection of annotated lines for one file."""

    path: Path
    lines: List[AnnotatedLine] = field(default_factory=list)

    def render(self) -> str:
        return "\n".join(line.render() for line in self.lines)

    @property
    def annotated_keys(self) -> List[str]:
        return [ln.key for ln in self.lines if ln.key and ln.note]


def annotate_env(
    path: Path,
    schema: Optional[EnvSchema] = None,
    include_lint: bool = True,
) -> AnnotationResult:
    """Return an AnnotationResult for *path*, attaching notes from schema/lint."""
    env_path = Path(path)
    parsed = parse_env_file(env_path)

    lint_issues: Dict[str, List[str]] = {}
    if include_lint:
        result = lint_env(env_path)
        for issue in result.issues:
            lint_issues.setdefault(issue.key, []).append(issue.code)

    schema_notes: Dict[str, str] = {}
    if schema:
        for key, rule in schema.rules.items():
            parts = []
            if rule.required:
                parts.append("required")
            if rule.pattern:
                parts.append(f"pattern={rule.pattern}")
            if rule.allowed_values:
                parts.append("enum=" + "|".join(rule.allowed_values))
            if parts:
                schema_notes[key] = ", ".join(parts)

    annotated_lines: List[AnnotatedLine] = []
    raw_text = env_path.read_text(encoding="utf-8")
    for raw_line in raw_text.splitlines():
        stripped = raw_line.strip()
        key: Optional[str] = None
        note_parts: List[str] = []

        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in lint_issues:
                note_parts.append("lint:" + ",".join(lint_issues[key]))
            if key in schema_notes:
                note_parts.append("schema:" + schema_notes[key])

        annotated_lines.append(
            AnnotatedLine(
                raw=raw_line,
                key=key,
                note="; ".join(note_parts) if note_parts else None,
            )
        )

    return AnnotationResult(path=env_path, lines=annotated_lines)
