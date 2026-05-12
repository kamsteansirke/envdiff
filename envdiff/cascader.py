"""Cascade multiple .env files in priority order, resolving final values."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from envdiff.parser import parse_env_file


@dataclass
class CascadeEntry:
    """A resolved key with its winning value and the source file that provided it."""

    key: str
    value: str
    source: str  # filename / label of the winning layer
    overridden_by: List[str] = field(default_factory=list)  # later layers that won

    def __str__(self) -> str:
        return f"{self.key}={self.value!r}  (from {self.source})"


@dataclass
class CascadeResult:
    """Result of cascading several env layers."""

    layers: List[str]  # ordered list of layer names (first = lowest priority)
    entries: Dict[str, CascadeEntry] = field(default_factory=dict)

    # keys that appear in at least two layers with different values
    overrides: List[str] = field(default_factory=list)

    @property
    def keys(self) -> List[str]:
        return sorted(self.entries.keys())

    def value_for(self, key: str) -> Optional[str]:
        entry = self.entries.get(key)
        return entry.value if entry else None

    def summary(self) -> str:
        lines = [
            f"Layers ({len(self.layers)}): {', '.join(self.layers)}",
            f"Total keys : {len(self.entries)}",
            f"Overridden : {len(self.overrides)}",
        ]
        return "\n".join(lines)


def cascade_envs(
    paths: Sequence[Path],
    labels: Optional[Sequence[str]] = None,
) -> CascadeResult:
    """Cascade *paths* from lowest to highest priority.

    The last file in *paths* wins conflicts.  *labels* are optional display
    names; if omitted the file names are used.
    """
    if labels is None:
        labels = [p.name for p in paths]
    if len(labels) != len(paths):
        raise ValueError("labels length must match paths length")

    layer_names = list(labels)
    result = CascadeResult(layers=layer_names)

    for path, label in zip(paths, labels):
        env = parse_env_file(path)
        for key, value in env.items():
            if key in result.entries:
                prev = result.entries[key]
                if prev.value != value:
                    # record which layer overrode it
                    prev.overridden_by.append(label)
                    if key not in result.overrides:
                        result.overrides.append(key)
                # update to the higher-priority (later) layer
                result.entries[key] = CascadeEntry(
                    key=key,
                    value=value,
                    source=label,
                    overridden_by=[],
                )
            else:
                result.entries[key] = CascadeEntry(key=key, value=value, source=label)

    result.overrides.sort()
    return result
