"""Resolve variable references within a .env file.

Given a parsed env dict, replace ${VAR} and $VAR references with their
resolved values, detecting circular and unresolvable references.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class ResolveIssue:
    key: str
    ref: str
    reason: str  # 'missing' | 'circular'

    def __str__(self) -> str:
        return f"{self.key}: ${{{self.ref}}} — {self.reason}"


@dataclass
class ResolveResult:
    resolved: Dict[str, str]
    issues: List[ResolveIssue] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.is_clean():
            return f"All {len(self.resolved)} keys resolved cleanly."
        lines = [f"{len(self.issues)} resolution issue(s):"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def _find_refs(value: str) -> List[str]:
    """Return all variable names referenced in *value*."""
    return [m.group(1) or m.group(2) for m in _REF_RE.finditer(value)]


def resolve_env(
    env: Dict[str, str],
    allow_missing: bool = False,
) -> ResolveResult:
    """Resolve all variable references in *env*.

    Parameters
    ----------
    env:
        Parsed key/value pairs (values may contain ``${VAR}`` references).
    allow_missing:
        When *True* leave unresolvable references as-is instead of recording
        an issue.
    """
    issues: List[ResolveIssue] = []
    cache: Dict[str, Optional[str]] = {}

    def _resolve(key: str, visiting: frozenset) -> str:
        if key in cache:
            return cache[key] or env.get(key, "")

        raw = env.get(key)
        if raw is None:
            return ""

        result = raw
        for ref in _find_refs(raw):
            if ref == key or ref in visiting:
                issues.append(ResolveIssue(key=key, ref=ref, reason="circular"))
                continue
            if ref not in env:
                if not allow_missing:
                    issues.append(ResolveIssue(key=key, ref=ref, reason="missing"))
                continue
            replacement = _resolve(ref, visiting | {key})
            result = re.sub(
                r"\$\{" + ref + r"\}|\$" + ref + r"(?=[^A-Za-z0-9_]|$)",
                replacement,
                result,
            )

        cache[key] = result
        return result

    resolved: Dict[str, str] = {}
    for k in env:
        resolved[k] = _resolve(k, frozenset())

    return ResolveResult(resolved=resolved, issues=issues)
