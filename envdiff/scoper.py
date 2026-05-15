"""Scope analysis: classify keys by deployment environment scope.

Detects keys that appear to be scoped to a specific environment
(e.g. DEV_, PROD_, STAGING_) and groups them accordingly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Well-known environment scope prefixes (case-insensitive match)
_KNOWN_SCOPES = [
    "DEV",
    "DEVELOPMENT",
    "PROD",
    "PRODUCTION",
    "STAGING",
    "STAGE",
    "TEST",
    "TESTING",
    "QA",
    "LOCAL",
    "CI",
    "SANDBOX",
]


@dataclass
class ScopeEntry:
    key: str
    scope: Optional[str]  # None means "global" / unscoped

    def __str__(self) -> str:
        tag = self.scope if self.scope else "global"
        return f"{self.key} [{tag}]"


@dataclass
class ScopeResult:
    entries: List[ScopeEntry] = field(default_factory=list)

    def scoped_keys(self) -> List[str]:
        """Return keys that carry an explicit scope prefix."""
        return sorted(e.key for e in self.entries if e.scope is not None)

    def global_keys(self) -> List[str]:
        """Return keys with no recognised scope prefix."""
        return sorted(e.key for e in self.entries if e.scope is None)

    def by_scope(self) -> Dict[str, List[str]]:
        """Return a mapping of scope -> sorted list of keys."""
        result: Dict[str, List[str]] = {}
        for e in self.entries:
            bucket = e.scope if e.scope else "global"
            result.setdefault(bucket, []).append(e.key)
        return {k: sorted(v) for k, v in sorted(result.items())}

    def summary(self) -> str:
        total = len(self.entries)
        scoped = len(self.scoped_keys())
        scopes = len([s for s in self.by_scope() if s != "global"])
        return (
            f"{total} keys total; {scoped} scoped across {scopes} scope(s); "
            f"{total - scoped} global"
        )


def _detect_scope(key: str) -> Optional[str]:
    """Return the scope prefix for *key*, or None if unscoped."""
    upper = key.upper()
    for scope in _KNOWN_SCOPES:
        if upper.startswith(scope + "_"):
            return scope
    return None


def scope_env(env: Dict[str, str]) -> ScopeResult:
    """Analyse *env* and return a :class:`ScopeResult`."""
    entries = [
        ScopeEntry(key=k, scope=_detect_scope(k))
        for k in sorted(env.keys())
    ]
    return ScopeResult(entries=entries)
