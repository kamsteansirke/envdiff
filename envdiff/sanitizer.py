"""Sanitize .env file values by detecting and fixing unsafe characters."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_TRAILING_WS_RE = re.compile(r"[ \t]+$")


@dataclass
class SanitizeIssue:
    key: str
    reason: str
    original: str
    fixed: Optional[str] = None

    def __str__(self) -> str:
        suffix = f" -> {self.fixed!r}" if self.fixed is not None else ""
        return f"{self.key}: {self.reason}{suffix}"


@dataclass
class SanitizeResult:
    issues: List[SanitizeIssue] = field(default_factory=list)
    sanitized: Dict[str, str] = field(default_factory=dict)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.is_clean:
            return "No sanitization issues found."
        lines = [f"{len(self.issues)} issue(s) found:"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def sanitize_env(
    env: Dict[str, str],
    *,
    fix_trailing_whitespace: bool = True,
    fix_control_chars: bool = True,
    strip_null_bytes: bool = True,
) -> SanitizeResult:
    """Scan *env* for unsafe values and return a SanitizeResult.

    The ``sanitized`` dict always contains the (possibly fixed) values.
    """
    issues: List[SanitizeIssue] = []
    sanitized: Dict[str, str] = {}

    for key, value in env.items():
        current = value

        if strip_null_bytes and "\x00" in current:
            fixed = current.replace("\x00", "")
            issues.append(SanitizeIssue(key, "null byte removed", current, fixed))
            current = fixed

        if fix_control_chars and _CONTROL_RE.search(current):
            fixed = _CONTROL_RE.sub("", current)
            issues.append(
                SanitizeIssue(key, "control characters removed", current, fixed)
            )
            current = fixed

        if fix_trailing_whitespace and _TRAILING_WS_RE.search(current):
            fixed = _TRAILING_WS_RE.sub("", current)
            issues.append(
                SanitizeIssue(key, "trailing whitespace removed", current, fixed)
            )
            current = fixed

        sanitized[key] = current

    return SanitizeResult(issues=issues, sanitized=sanitized)
