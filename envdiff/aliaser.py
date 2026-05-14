"""aliaser.py – detect keys that appear to be aliases of each other.

Two keys are considered aliases when they share the same non-empty value
across a parsed env mapping.  This is distinct from duplicate *keys*
(handled by deduplicator) – here the keys are different but the values
are identical, suggesting one may be a legacy alias for the other.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class AliasGroup:
    """A set of keys that all share the same value."""

    value: str
    keys: List[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        keys_fmt = ", ".join(sorted(self.keys))
        return f"[{keys_fmt}] -> {self.value!r}"


@dataclass
class AliasResult:
    groups: List[AliasGroup] = field(default_factory=list)

    @property
    def has_aliases(self) -> bool:
        return bool(self.groups)

    @property
    def total_alias_keys(self) -> int:
        """Total number of keys involved in any alias group."""
        return sum(len(g.keys) for g in self.groups)

    def summary(self) -> str:
        if not self.has_aliases:
            return "No alias groups detected."
        lines = [f"{len(self.groups)} alias group(s) found:"]
        for g in self.groups:
            keys_fmt = ", ".join(sorted(g.keys))
            lines.append(f"  {keys_fmt}  (value={g.value!r})")
        return "\n".join(lines)


def find_aliases(
    env: Dict[str, str],
    *,
    ignore_empty: bool = True,
    min_group_size: int = 2,
) -> AliasResult:
    """Return an :class:`AliasResult` describing keys that share identical values.

    Parameters
    ----------
    env:
        Parsed key/value mapping (e.g. from :func:`envdiff.parser.parse_env_file`).
    ignore_empty:
        When *True* (default), keys with empty-string values are excluded so
        that unset placeholders are not falsely grouped together.
    min_group_size:
        Minimum number of keys required to form a group (default 2).
    """
    value_to_keys: Dict[str, List[str]] = {}
    for key, value in env.items():
        if ignore_empty and value == "":
            continue
        value_to_keys.setdefault(value, []).append(key)

    groups: List[AliasGroup] = [
        AliasGroup(value=val, keys=sorted(keys))
        for val, keys in sorted(value_to_keys.items())
        if len(keys) >= min_group_size
    ]
    return AliasResult(groups=groups)
