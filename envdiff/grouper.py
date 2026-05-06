"""Group and categorize env keys by prefix or naming convention."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GroupResult:
    """Result of grouping env keys by prefix."""
    groups: Dict[str, List[str]] = field(default_factory=dict)
    ungrouped: List[str] = field(default_factory=list)

    def group_names(self) -> List[str]:
        """Return sorted list of group names."""
        return sorted(self.groups.keys())

    def summary(self) -> str:
        lines = []
        for name in self.group_names():
            keys = self.groups[name]
            lines.append(f"[{name}] {len(keys)} key(s): {', '.join(sorted(keys))}")
        if self.ungrouped:
            lines.append(f"[ungrouped] {len(self.ungrouped)} key(s): {', '.join(sorted(self.ungrouped))}")
        return "\n".join(lines) if lines else "(no keys)"


def group_by_prefix(
    keys: List[str],
    separator: str = "_",
    min_group_size: int = 1,
    max_prefix_parts: int = 1,
) -> GroupResult:
    """Group keys by their prefix (parts before the first separator).

    Args:
        keys: List of env key names.
        separator: Character used to split key names.
        min_group_size: Minimum number of keys required to form a group.
        max_prefix_parts: How many prefix segments to use as the group name.

    Returns:
        GroupResult with grouped and ungrouped keys.
    """
    from collections import defaultdict

    buckets: Dict[str, List[str]] = defaultdict(list)

    for key in keys:
        parts = key.split(separator)
        if len(parts) > max_prefix_parts:
            prefix = separator.join(parts[:max_prefix_parts])
        else:
            prefix = None

        if prefix:
            buckets[prefix].append(key)
        else:
            buckets[""].append(key)

    groups: Dict[str, List[str]] = {}
    ungrouped: List[str] = []

    for prefix, members in buckets.items():
        if not prefix or len(members) < min_group_size:
            ungrouped.extend(members)
        else:
            groups[prefix] = members

    return GroupResult(groups=groups, ungrouped=ungrouped)


def group_env(
    env: Dict[str, Optional[str]],
    separator: str = "_",
    min_group_size: int = 2,
) -> GroupResult:
    """Convenience wrapper: group an env dict's keys by prefix."""
    return group_by_prefix(
        list(env.keys()),
        separator=separator,
        min_group_size=min_group_size,
    )
