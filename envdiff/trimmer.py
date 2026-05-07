"""trimmer.py – Detect and strip leading/trailing whitespace from .env values."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

from envdiff.parser import parse_env_file


@dataclass
class TrimIssue:
    key: str
    original: str
    trimmed: str

    def __str__(self) -> str:
        return f"{self.key}: {self.original!r} -> {self.trimmed!r}"


@dataclass
class TrimResult:
    path: Path
    issues: List[TrimIssue] = field(default_factory=list)
    cleaned: Dict[str, str] = field(default_factory=dict)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.is_clean:
            return f"{self.path}: no whitespace issues found"
        lines = [f"{self.path}: {len(self.issues)} key(s) with surrounding whitespace"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def trim_env(path: Path) -> TrimResult:
    """Parse *path* and detect values with leading/trailing whitespace."""
    env = parse_env_file(path)
    issues: List[TrimIssue] = []
    cleaned: Dict[str, str] = {}

    for key, value in env.items():
        trimmed = value.strip()
        cleaned[key] = trimmed
        if trimmed != value:
            issues.append(TrimIssue(key=key, original=value, trimmed=trimmed))

    return TrimResult(path=path, issues=issues, cleaned=cleaned)


def apply_trim(path: Path, result: TrimResult) -> List[Tuple[int, str]]:
    """Rewrite *path* in-place, replacing values that have surrounding whitespace.

    Returns a list of (line_number, new_line) tuples for every line changed.
    """
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed: List[Tuple[int, str]] = []
    trimmed_keys = {issue.key: issue.trimmed for issue in result.issues}

    new_lines = []
    for i, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if stripped.startswith("#") or "=" not in stripped:
            new_lines.append(raw)
            continue
        key, _, _ = stripped.partition("=")
        key = key.strip()
        if key in trimmed_keys:
            new_line = f"{key}={trimmed_keys[key]}\n"
            new_lines.append(new_line)
            changed.append((i, new_line))
        else:
            new_lines.append(raw)

    path.write_text("".join(new_lines), encoding="utf-8")
    return changed
