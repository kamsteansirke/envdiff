"""Strip comments and blank lines from .env files, returning a cleaned mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envdiff.parser import parse_env_file


@dataclass
class StripIssue:
    line_number: int
    original: str
    reason: str  # 'blank' | 'comment' | 'whitespace'

    def __str__(self) -> str:
        return f"L{self.line_number}: [{self.reason}] {self.original!r}"


@dataclass
class StripResult:
    path: Path
    cleaned: Dict[str, str]
    issues: List[StripIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.is_clean:
            return f"{self.path}: no strippable lines found"
        counts: Dict[str, int] = {}
        for issue in self.issues:
            counts[issue.reason] = counts.get(issue.reason, 0) + 1
        parts = ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
        return f"{self.path}: {len(self.issues)} strippable line(s) ({parts})"

    def render(self) -> str:
        """Return a cleaned .env file as a string."""
        lines = []
        for key, value in self.cleaned.items():
            if " " in value or value == "":
                lines.append(f'{key}="{value}"')
            else:
                lines.append(f"{key}={value}")
        return "\n".join(lines) + ("\n" if lines else "")


def strip_env(path: Path) -> StripResult:
    """Parse *path*, record blank/comment/whitespace-only lines, return cleaned result."""
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    issues: List[StripIssue] = []

    for lineno, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if stripped == "":
            issues.append(StripIssue(lineno, raw, "blank"))
        elif stripped.startswith("#"):
            issues.append(StripIssue(lineno, raw, "comment"))
        elif raw != stripped and "=" not in stripped:
            issues.append(StripIssue(lineno, raw, "whitespace"))

    cleaned = parse_env_file(path)
    return StripResult(path=path, cleaned=cleaned, issues=issues)
