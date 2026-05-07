"""Normalize .env file contents: trim whitespace, sort keys, enforce casing."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file


class CasePolicy(str, Enum):
    UPPER = "upper"
    LOWER = "lower"
    PRESERVE = "preserve"


@dataclass
class NormalizeOptions:
    sort_keys: bool = True
    case_policy: CasePolicy = CasePolicy.PRESERVE
    strip_empty_values: bool = False


@dataclass
class NormalizeResult:
    original: Dict[str, str]
    normalized: Dict[str, str]
    changes: List[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.changes) == 0

    def summary(self) -> str:
        if self.is_clean:
            return "No normalization changes required."
        lines = [f"{len(self.changes)} change(s):"]
        for c in self.changes:
            lines.append(f"  - {c}")
        return "\n".join(lines)


def normalize_env(
    path: str,
    options: Optional[NormalizeOptions] = None,
) -> NormalizeResult:
    """Parse *path* and apply normalization rules, returning a NormalizeResult."""
    if options is None:
        options = NormalizeOptions()

    original: Dict[str, str] = parse_env_file(path)
    normalized: Dict[str, str] = {}
    changes: List[str] = []

    items = list(original.items())

    for key, value in items:
        new_key = key
        if options.case_policy == CasePolicy.UPPER and key != key.upper():
            changes.append(f"key casing: {key!r} -> {key.upper()!r}")
            new_key = key.upper()
        elif options.case_policy == CasePolicy.LOWER and key != key.lower():
            changes.append(f"key casing: {key!r} -> {key.lower()!r}")
            new_key = key.lower()

        stripped = value.strip()
        if stripped != value:
            changes.append(f"whitespace stripped for key {new_key!r}")
            value = stripped

        if options.strip_empty_values and value == "":
            changes.append(f"empty value removed for key {new_key!r}")
            continue

        normalized[new_key] = value

    if options.sort_keys:
        sorted_normalized = dict(sorted(normalized.items()))
        if list(sorted_normalized.keys()) != list(normalized.keys()):
            changes.append("keys reordered alphabetically")
        normalized = sorted_normalized

    return NormalizeResult(original=original, normalized=normalized, changes=changes)


def render_normalized(result: NormalizeResult) -> str:
    """Render the normalized key=value pairs as a .env-formatted string."""
    lines = [f"{k}={v}" for k, v in result.normalized.items()]
    return "\n".join(lines) + ("\n" if lines else "")
