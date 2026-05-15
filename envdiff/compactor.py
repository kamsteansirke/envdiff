"""compactor.py – Remove redundant or overridden keys from a layered env set.

A key is considered *redundant* in a lower-priority file when every
higher-priority file already defines it with the same value.  A key is
*overridden* when a higher-priority file redefines it with a *different*
value, making the lower-priority definition effectively dead.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence


@dataclass
class CompactIssue:
    key: str
    source: str          # filename where the redundant/overridden key lives
    kind: str            # "redundant" | "overridden"
    overriding_source: Optional[str] = None  # which file wins

    def __str__(self) -> str:
        if self.kind == "overridden":
            return (
                f"{self.key!r} in '{self.source}' is overridden by '{self.overriding_source}'"
            )
        return f"{self.key!r} in '{self.source}' is redundant (same value in higher-priority env)"


@dataclass
class CompactResult:
    issues: List[CompactIssue] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def summary(self) -> str:
        if self.is_clean:
            return "No redundant or overridden keys found."
        redundant = sum(1 for i in self.issues if i.kind == "redundant")
        overridden = sum(1 for i in self.issues if i.kind == "overridden")
        parts: List[str] = []
        if redundant:
            parts.append(f"{redundant} redundant")
        if overridden:
            parts.append(f"{overridden} overridden")
        return f"{len(self.issues)} issue(s): {', '.join(parts)}."

    def by_source(self) -> Dict[str, List[CompactIssue]]:
        result: Dict[str, List[CompactIssue]] = {}
        for issue in self.issues:
            result.setdefault(issue.source, []).append(issue)
        return result


def compact_envs(
    layers: Sequence[Dict[str, str]],
    names: Sequence[str],
) -> CompactResult:
    """Analyse *layers* (highest priority first) for redundant/overridden keys.

    Args:
        layers: Ordered sequence of parsed env dicts, index 0 = highest priority.
        names:  Human-readable label for each layer (same length as *layers*).
    """
    if len(layers) != len(names):
        raise ValueError("layers and names must have the same length")

    issues: List[CompactIssue] = []

    # For every layer except the highest-priority one, check each key.
    for idx in range(1, len(layers)):
        current = layers[idx]
        current_name = names[idx]
        higher = layers[:idx]          # all layers with higher priority
        higher_names = names[:idx]

        for key, value in current.items():
            for h_idx, h_layer in enumerate(higher):
                if key in h_layer:
                    if h_layer[key] == value:
                        issues.append(
                            CompactIssue(
                                key=key,
                                source=current_name,
                                kind="redundant",
                                overriding_source=higher_names[h_idx],
                            )
                        )
                    else:
                        issues.append(
                            CompactIssue(
                                key=key,
                                source=current_name,
                                kind="overridden",
                                overriding_source=higher_names[h_idx],
                            )
                        )
                    break  # report against the first (highest-priority) match only

    return CompactResult(issues=issues)
