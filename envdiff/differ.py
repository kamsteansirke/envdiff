"""Unified diff output for .env file changes between two snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LineDiff:
    """Represents a single changed, added, or removed key."""

    key: str
    status: str  # 'added' | 'removed' | 'changed'
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def __str__(self) -> str:
        if self.status == "added":
            return f"+ {self.key}={self.new_value}"
        if self.status == "removed":
            return f"- {self.key}={self.old_value}"
        return f"~ {self.key}: {self.old_value!r} -> {self.new_value!r}"


@dataclass
class SnapshotDiff:
    """Full diff between two env snapshots."""

    added: List[LineDiff] = field(default_factory=list)
    removed: List[LineDiff] = field(default_factory=list)
    changed: List[LineDiff] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)

    @property
    def all_changes(self) -> List[LineDiff]:
        return self.removed + self.added + self.changed


def diff_snapshots(
    before: Dict[str, str],
    after: Dict[str, str],
) -> SnapshotDiff:
    """Compute the diff between two env snapshots (key->value dicts).

    Args:
        before: The earlier snapshot.
        after:  The later snapshot.

    Returns:
        A :class:`SnapshotDiff` describing what changed.
    """
    result = SnapshotDiff()

    all_keys = set(before) | set(after)
    for key in sorted(all_keys):
        in_before = key in before
        in_after = key in after

        if in_before and not in_after:
            result.removed.append(
                LineDiff(key=key, status="removed", old_value=before[key])
            )
        elif in_after and not in_before:
            result.added.append(
                LineDiff(key=key, status="added", new_value=after[key])
            )
        elif before[key] != after[key]:
            result.changed.append(
                LineDiff(
                    key=key,
                    status="changed",
                    old_value=before[key],
                    new_value=after[key],
                )
            )

    return result
