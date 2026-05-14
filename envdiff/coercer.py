"""Type coercion analysis for .env values.

Detects the inferred type of each value (bool, int, float, url, empty, string)
and reports keys whose values cannot be cleanly coerced to their apparent type.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+\.\d+$")
_BOOL_TRUE = {"true", "yes", "1", "on"}
_BOOL_FALSE = {"false", "no", "0", "off"}


def infer_type(value: str) -> str:
    """Return a string label for the inferred type of *value*."""
    if value == "":
        return "empty"
    low = value.lower()
    if low in _BOOL_TRUE or low in _BOOL_FALSE:
        return "bool"
    if _INT_RE.match(value):
        return "int"
    if _FLOAT_RE.match(value):
        return "float"
    if _URL_RE.match(value):
        return "url"
    return "string"


@dataclass
class CoerceEntry:
    key: str
    value: str
    inferred_type: str

    def __str__(self) -> str:
        return f"{self.key}={self.value!r} ({self.inferred_type})"


@dataclass
class CoerceResult:
    entries: List[CoerceEntry] = field(default_factory=list)

    def by_type(self, type_label: str) -> List[CoerceEntry]:
        """Return all entries whose inferred type matches *type_label*."""
        return [e for e in self.entries if e.inferred_type == type_label]

    def type_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self.entries:
            counts[e.inferred_type] = counts.get(e.inferred_type, 0) + 1
        return counts

    def summary(self) -> str:
        if not self.entries:
            return "No keys found."
        counts = self.type_counts()
        parts = ", ".join(
            f"{t}: {n}" for t, n in sorted(counts.items())
        )
        return f"{len(self.entries)} key(s) — {parts}"


def coerce_env(env: Dict[str, str]) -> CoerceResult:
    """Analyse *env* and return a :class:`CoerceResult`."""
    entries = [
        CoerceEntry(key=k, value=v, inferred_type=infer_type(v))
        for k, v in sorted(env.items())
    ]
    return CoerceResult(entries=entries)
