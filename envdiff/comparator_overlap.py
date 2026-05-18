"""Overlap analysis: find keys shared across multiple env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional

from envdiff.parser import parse_env_file


@dataclass
class OverlapEntry:
    """A key and the set of env files it appears in."""

    key: str
    present_in: FrozenSet[str]  # env file stems

    def coverage(self, total: int) -> float:
        """Fraction of files that contain this key (0.0 – 1.0)."""
        if total == 0:
            return 0.0
        return len(self.present_in) / total

    def __str__(self) -> str:
        sources = ", ".join(sorted(self.present_in))
        return f"{self.key} [{sources}]"


@dataclass
class OverlapResult:
    """Overlap analysis across *n* env files."""

    env_names: List[str]
    _entries: Dict[str, OverlapEntry] = field(default_factory=dict, repr=False)

    # --- accessors ---

    def all_keys(self) -> List[str]:
        return sorted(self._entries)

    def universal_keys(self) -> List[str]:
        """Keys present in every env file."""
        total = len(self.env_names)
        return [k for k, e in sorted(self._entries.items()) if len(e.present_in) == total]

    def unique_keys(self) -> List[str]:
        """Keys that appear in exactly one env file."""
        return [k for k, e in sorted(self._entries.items()) if len(e.present_in) == 1]

    def entry_for(self, key: str) -> Optional[OverlapEntry]:
        return self._entries.get(key)

    def is_fully_overlapping(self) -> bool:
        """True when every key appears in every file."""
        return len(self.universal_keys()) == len(self._entries)

    def summary(self) -> str:
        total = len(self._entries)
        universal = len(self.universal_keys())
        unique = len(self.unique_keys())
        return (
            f"{total} keys across {len(self.env_names)} files | "
            f"{universal} universal | {unique} unique-to-one"
        )


def analyze_overlap(*paths: Path) -> OverlapResult:
    """Parse each path and compute per-key presence across all files."""
    envs: Dict[str, Dict[str, str]] = {}
    for p in paths:
        envs[p.stem] = parse_env_file(p)

    env_names = sorted(envs)
    result = OverlapResult(env_names=env_names)

    all_keys: FrozenSet[str] = frozenset(k for env in envs.values() for k in env)
    for key in all_keys:
        present = frozenset(name for name, env in envs.items() if key in env)
        result._entries[key] = OverlapEntry(key=key, present_in=present)

    return result
