"""Lint .env files for common style and correctness issues."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envdiff.parser import parse_env_file

_UPPER_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')
_NO_SPACE_RE = re.compile(r'^[^\s=]+=.*$')


@dataclass
class LintIssue:
    line_no: int
    key: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"line {self.line_no}: [{self.code}] {self.key!r} — {self.message}"


@dataclass
class LintResult:
    path: Path
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.passed:
            return f"{self.path}: OK"
        lines = [f"{self.path}: {len(self.issues)} issue(s)"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def lint_env(path: Path, *, require_uppercase: bool = True,
             forbid_empty_values: bool = False) -> LintResult:
    """Lint a single .env file and return a LintResult."""
    result = LintResult(path=path)

    raw_lines: list[str] = []
    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        result.issues.append(LintIssue(0, "", "E000", f"Cannot read file: {exc}"))
        return result

    try:
        parsed = parse_env_file(path)
    except Exception as exc:  # noqa: BLE001
        result.issues.append(LintIssue(0, "", "E001", f"Parse error: {exc}"))
        return result

    key_line: dict[str, int] = {}
    for lineno, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            key_line[key] = lineno

    seen: set[str] = set()
    for key, value in parsed.items():
        lineno = key_line.get(key, 0)

        if key in seen:
            result.issues.append(LintIssue(lineno, key, "W001", "Duplicate key"))
        seen.add(key)

        if require_uppercase and not _UPPER_RE.match(key):
            result.issues.append(
                LintIssue(lineno, key, "W002",
                          "Key should be UPPER_SNAKE_CASE")
            )

        if forbid_empty_values and value == "":
            result.issues.append(
                LintIssue(lineno, key, "W003", "Empty value")
            )

    return result
