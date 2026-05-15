"""Pivot multiple env files into a key-centric view.

Given N env files, build a table where each row is a key and each column is
an environment.  This makes it easy to spot which environments define a key
and whether the values agree.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

SENTINEL = object()  # marks a key absent in a given environment


@dataclass
class PivotRow:
    """One row in the pivot table — a single key across all environments."""

    key: str
    values: Dict[str, Optional[str]]  # env_name -> value (None = absent)

    @property
    def env_names(self) -> List[str]:
        return sorted(self.values)

    def present_in(self) -> List[str]:
        """Environments where this key is defined."""
        return [name for name, v in self.values.items() if v is not None]

    def absent_in(self) -> List[str]:
        """Environments where this key is missing."""
        return [name for name, v in self.values.items() if v is None]

    def is_consistent(self) -> bool:
        """Return True if all *present* environments share the same value."""
        present_vals = {v for v in self.values.values() if v is not None}
        return len(present_vals) <= 1

    def is_universal(self) -> bool:
        """Return True if the key is present in every environment."""
        return all(v is not None for v in self.values.values())


@dataclass
class PivotTable:
    """Full pivot of N env files."""

    env_names: List[str]
    rows: List[PivotRow] = field(default_factory=list)

    def all_keys(self) -> List[str]:
        return [r.key for r in self.rows]

    def inconsistent_rows(self) -> List[PivotRow]:
        return [r for r in self.rows if not r.is_consistent()]

    def missing_rows(self) -> List[PivotRow]:
        """Rows where at least one env is missing the key."""
        return [r for r in self.rows if not r.is_universal()]

    def summary(self) -> str:
        total = len(self.rows)
        inconsistent = len(self.inconsistent_rows())
        missing = len(self.missing_rows())
        envs = len(self.env_names)
        return (
            f"{total} keys across {envs} environments; "
            f"{missing} with gaps, {inconsistent} with value mismatches"
        )


def pivot_envs(envs: Dict[str, Dict[str, str]]) -> PivotTable:
    """Build a :class:`PivotTable` from a mapping of env-name -> parsed dict."""
    env_names = sorted(envs)
    all_keys: Set[str] = set()
    for parsed in envs.values():
        all_keys.update(parsed)

    rows: List[PivotRow] = []
    for key in sorted(all_keys):
        values = {name: envs[name].get(key) for name in env_names}
        rows.append(PivotRow(key=key, values=values))

    return PivotTable(env_names=env_names, rows=rows)
