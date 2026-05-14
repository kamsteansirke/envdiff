"""requirer.py – Check that a set of required keys are present in an env mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass
class RequireIssue:
    key: str
    reason: str = "missing required key"

    def __str__(self) -> str:
        return f"{self.key}: {self.reason}"


@dataclass
class RequireResult:
    source: str
    issues: List[RequireIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.is_clean():
            return f"{self.source}: all required keys present"
        keys = ", ".join(i.key for i in self.issues)
        return f"{self.source}: {len(self.issues)} missing required key(s): {keys}"

    def missing_keys(self) -> List[str]:
        return [i.key for i in self.issues]


def require_keys(
    env: Dict[str, str],
    required: Iterable[str],
    *,
    source: str = "<env>",
    allow_empty: bool = True,
) -> RequireResult:
    """Return a RequireResult describing which required keys are absent.

    Parameters
    ----------
    env:
        Parsed key/value mapping.
    required:
        Iterable of key names that must be present.
    source:
        Label used in the result (e.g. a filename).
    allow_empty:
        When *False*, a key that is present but has an empty string value is
        also reported as missing.
    """
    issues: List[RequireIssue] = []
    for key in required:
        if key not in env:
            issues.append(RequireIssue(key=key, reason="missing required key"))
        elif not allow_empty and env[key] == "":
            issues.append(RequireIssue(key=key, reason="required key has empty value"))
    return RequireResult(source=source, issues=issues)
