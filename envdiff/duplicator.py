"""Detect and report duplicate values across keys in a .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.parser import parse_env_file


@dataclass
class ValueCluster:
    """A group of keys that share the same value."""

    value: str
    keys: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.value!r} shared by: {', '.join(sorted(self.keys))}"


@dataclass
class DuplicateValueResult:
    """Result of scanning a file for duplicate values."""

    path: str
    clusters: List[ValueCluster] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return len(self.clusters) > 0

    def summary(self) -> str:
        if not self.has_duplicates:
            return f"{self.path}: no duplicate values found"
        lines = [f"{self.path}: {len(self.clusters)} duplicate value group(s)"]
        for cluster in self.clusters:
            lines.append(f"  {cluster}")
        return "\n".join(lines)


def find_duplicate_values(
    path: str,
    ignore_empty: bool = True,
) -> DuplicateValueResult:
    """Scan *path* and return keys that share identical values."""
    env = parse_env_file(path)

    value_map: Dict[str, List[str]] = {}
    for key, value in env.items():
        if ignore_empty and value == "":
            continue
        value_map.setdefault(value, []).append(key)

    clusters = [
        ValueCluster(value=v, keys=keys)
        for v, keys in value_map.items()
        if len(keys) > 1
    ]
    clusters.sort(key=lambda c: c.value)

    return DuplicateValueResult(path=path, clusters=clusters)
