"""Detect and resolve variable interpolation references in .env files."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_REF_RE = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolationIssue:
    key: str
    ref: str
    message: str

    def __str__(self) -> str:
        return f"{self.key}: {self.message} (ref: ${self.ref})"


@dataclass
class InterpolationResult:
    resolved: Dict[str, str] = field(default_factory=dict)
    issues: List[InterpolationIssue] = field(default_factory=list)
    unresolved_refs: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.is_clean:
            return "All interpolations resolved cleanly."
        lines = [f"{len(self.issues)} interpolation issue(s) found:"]
        for issue in self.issues:
            lines.append(f"  - {issue}")
        return "\n".join(lines)


def _find_refs(value: str) -> List[str]:
    """Return all variable names referenced in *value*."""
    refs: List[str] = []
    for m in _REF_RE.finditer(value):
        refs.append(m.group(1) or m.group(2))
    return refs


def interpolate_env(
    env: Dict[str, str],
    external: Optional[Dict[str, str]] = None,
) -> InterpolationResult:
    """Resolve ``${VAR}`` / ``$VAR`` references in *env* values.

    Parameters
    ----------
    env:
        Parsed key/value mapping from a single .env file.
    external:
        Additional variables available for resolution (e.g. OS environment).
        Keys in *env* take precedence.
    """
    lookup: Dict[str, str] = dict(external or {})
    lookup.update(env)

    result = InterpolationResult()

    for key, raw_value in env.items():
        refs = _find_refs(raw_value)
        if not refs:
            result.resolved[key] = raw_value
            continue

        resolved_value = raw_value
        missing: List[str] = []
        for ref in refs:
            if ref in lookup:
                pattern = re.compile(
                    r"\$\{" + re.escape(ref) + r"\}|\$" + re.escape(ref) + r"(?![A-Za-z0-9_])"
                )
                resolved_value = pattern.sub(lookup[ref], resolved_value)
            else:
                missing.append(ref)

        if missing:
            result.unresolved_refs[key] = missing
            for ref in missing:
                result.issues.append(
                    InterpolationIssue(
                        key=key,
                        ref=ref,
                        message=f"unresolved reference '${ref}'",
                    )
                )
        result.resolved[key] = resolved_value

    return result
