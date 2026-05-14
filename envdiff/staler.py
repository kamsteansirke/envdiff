"""Staleness detection: flag keys whose values look outdated or placeholder-like."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_PLACEHOLDER_PATTERNS: List[re.Pattern] = [
    re.compile(r'^(change_?me|changeme|replace_?me|todo|fixme|xxx|placeholder|your[_-]?\w+here)$', re.I),
    re.compile(r'^<[^>]+>$'),          # <YOUR_VALUE>
    re.compile(r'^\$\{[^}]+\}$'),     # ${UNRESOLVED_VAR}
    re.compile(r'^\[.*\]$'),           # [fill this in]
    re.compile(r'^example[._-]', re.I),
    re.compile(r'example\.com', re.I),
    re.compile(r'localhost', re.I),
    re.compile(r'^0\.0\.0\.0$'),
    re.compile(r'^(none|null|nil|undefined|n/?a)$', re.I),
]


@dataclass
class StaleIssue:
    key: str
    value: str
    reason: str

    def __str__(self) -> str:
        return f"{self.key}: {self.reason} (value={self.value!r})"


@dataclass
class StaleResult:
    issues: List[StaleIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.is_clean:
            return "No stale values detected."
        lines = [f"{len(self.issues)} stale value(s) detected:"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def _detect_placeholder(value: str) -> Optional[str]:
    """Return a reason string if the value looks like a placeholder, else None."""
    for pattern in _PLACEHOLDER_PATTERNS:
        if pattern.search(value):
            return f"matches placeholder pattern '{pattern.pattern}'"
    return None


def check_staleness(env: Dict[str, str]) -> StaleResult:
    """Inspect every key/value pair and return a StaleResult."""
    issues: List[StaleIssue] = []
    for key, value in env.items():
        reason = _detect_placeholder(value)
        if reason:
            issues.append(StaleIssue(key=key, value=value, reason=reason))
    return StaleResult(issues=issues)
