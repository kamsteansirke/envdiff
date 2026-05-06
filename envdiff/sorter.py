"""Sort and reorder .env file keys by various strategies."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class SortStrategy(str, Enum):
    ALPHA = "alpha"          # A-Z alphabetical
    ALPHA_DESC = "alpha_desc"  # Z-A reverse alphabetical
    LENGTH = "length"        # shortest key first
    GROUP = "group"          # group by prefix, then alpha within group


@dataclass
class SortResult:
    strategy: SortStrategy
    original_order: List[str]
    sorted_order: List[str]
    groups: Dict[str, List[str]] = field(default_factory=dict)  # only for GROUP

    @property
    def changed(self) -> bool:
        """Return True if sorted order differs from original."""
        return self.original_order != self.sorted_order

    def summary(self) -> str:
        lines = [
            f"Strategy : {self.strategy.value}",
            f"Keys     : {len(self.sorted_order)}",
            f"Reordered: {'yes' if self.changed else 'no'}",
        ]
        if self.strategy == SortStrategy.GROUP and self.groups:
            lines.append("Groups   :")
            for prefix, keys in sorted(self.groups.items()):
                label = prefix if prefix else "(ungrouped)"
                lines.append(f"  {label}: {len(keys)} key(s)")
        return "\n".join(lines)


def _prefix(key: str, sep: str = "_") -> str:
    """Return the first segment of a key before the separator."""
    if sep in key:
        return key.split(sep, 1)[0]
    return ""


def sort_env(
    env: Dict[str, str],
    strategy: SortStrategy = SortStrategy.ALPHA,
    prefix_sep: str = "_",
    group_order: Optional[List[str]] = None,
) -> SortResult:
    """Sort *env* keys according to *strategy* and return a SortResult.

    Parameters
    ----------
    env:
        Mapping of key -> value as returned by ``parse_env_file``.
    strategy:
        One of the SortStrategy enum values.
    prefix_sep:
        Separator used to detect key prefixes when strategy is GROUP.
    group_order:
        Optional explicit ordering of group prefixes for GROUP strategy.
        Prefixes not listed appear after those that are.
    """
    original = list(env.keys())

    if strategy == SortStrategy.ALPHA:
        sorted_keys = sorted(original)
        return SortResult(strategy, original, sorted_keys)

    if strategy == SortStrategy.ALPHA_DESC:
        sorted_keys = sorted(original, reverse=True)
        return SortResult(strategy, original, sorted_keys)

    if strategy == SortStrategy.LENGTH:
        sorted_keys = sorted(original, key=lambda k: (len(k), k))
        return SortResult(strategy, original, sorted_keys)

    # GROUP strategy
    groups: Dict[str, List[str]] = {}
    for key in original:
        p = _prefix(key, prefix_sep)
        groups.setdefault(p, []).append(key)

    # Sort keys within each group
    for p in groups:
        groups[p].sort()

    # Determine group ordering
    if group_order:
        ordered_prefixes = [p for p in group_order if p in groups]
        remaining = sorted(p for p in groups if p not in group_order)
        all_prefixes = ordered_prefixes + remaining
    else:
        # ungrouped ("") goes last
        named = sorted(p for p in groups if p)
        all_prefixes = named + (["" ] if "" in groups else [])

    sorted_keys = [k for p in all_prefixes for k in groups[p]]
    return SortResult(strategy, original, sorted_keys, groups)
