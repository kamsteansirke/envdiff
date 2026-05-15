"""Detect deprecated or sunset keys in .env files based on a deprecation registry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DeprecationIssue:
    key: str
    reason: str
    replacement: Optional[str] = None

    def __str__(self) -> str:
        msg = f"{self.key}: {self.reason}"
        if self.replacement:
            msg += f" (use '{self.replacement}' instead)"
        return msg


@dataclass
class DeprecationResult:
    issues: List[DeprecationIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.is_clean():
            return "No deprecated keys found."
        lines = [f"{len(self.issues)} deprecated key(s) detected:"]
        for issue in sorted(self.issues, key=lambda i: i.key):
            lines.append(f"  - {issue}")
        return "\n".join(lines)

    def keys(self) -> List[str]:
        return sorted(i.key for i in self.issues)


def check_deprecations(
    env: Dict[str, str],
    registry: Dict[str, Dict],
) -> DeprecationResult:
    """Check *env* against a *registry* of deprecated key definitions.

    Each registry entry maps a key name to a dict with:
      - ``reason`` (str, required): human-readable explanation.
      - ``replacement`` (str, optional): suggested replacement key.

    Example registry::

        {
            "OLD_API_KEY": {"reason": "Renamed", "replacement": "API_KEY"},
            "LEGACY_MODE": {"reason": "Feature removed"},
        }
    """
    issues: List[DeprecationIssue] = []
    for key in env:
        if key in registry:
            entry = registry[key]
            issues.append(
                DeprecationIssue(
                    key=key,
                    reason=entry.get("reason", "Deprecated"),
                    replacement=entry.get("replacement"),
                )
            )
    return DeprecationResult(issues=issues)
