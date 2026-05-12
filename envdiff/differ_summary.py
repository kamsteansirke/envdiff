"""Summarise a SnapshotDiff into human-readable text and structured data."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.differ import SnapshotDiff, LineDiff


@dataclass
class DiffSummaryEntry:
    key: str
    change_type: str  # 'added' | 'removed' | 'changed'
    old_value: str | None = None
    new_value: str | None = None

    def __str__(self) -> str:
        if self.change_type == "added":
            return f"+ {self.key}"
        if self.change_type == "removed":
            return f"- {self.key}"
        return f"~ {self.key}  ({self.old_value!r} -> {self.new_value!r})"


@dataclass
class DiffSummaryReport:
    entries: List[DiffSummaryEntry] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.entries) == 0

    @property
    def added(self) -> List[DiffSummaryEntry]:
        return [e for e in self.entries if e.change_type == "added"]

    @property
    def removed(self) -> List[DiffSummaryEntry]:
        return [e for e in self.entries if e.change_type == "removed"]

    @property
    def changed(self) -> List[DiffSummaryEntry]:
        return [e for e in self.entries if e.change_type == "changed"]

    def render(self, show_values: bool = False) -> str:
        if self.is_empty:
            return "No changes detected."
        lines: List[str] = []
        for entry in self.entries:
            if show_values:
                lines.append(str(entry))
            else:
                prefix = {"added": "+", "removed": "-", "changed": "~"}[entry.change_type]
                lines.append(f"{prefix} {entry.key}")
        added_n = len(self.added)
        removed_n = len(self.removed)
        changed_n = len(self.changed)
        lines.append(
            f"\nSummary: {added_n} added, {removed_n} removed, {changed_n} changed."
        )
        return "\n".join(lines)


def summarise_diff(diff: SnapshotDiff, show_values: bool = False) -> DiffSummaryReport:
    """Convert a SnapshotDiff into a DiffSummaryReport."""
    entries: List[DiffSummaryEntry] = []
    for line_diff in diff.all_changes():
        entry = _line_diff_to_entry(line_diff)
        entries.append(entry)
    return DiffSummaryReport(entries=entries)


def _line_diff_to_entry(ld: LineDiff) -> DiffSummaryEntry:
    if ld.old_value is None:
        return DiffSummaryEntry(key=ld.key, change_type="added", new_value=ld.new_value)
    if ld.new_value is None:
        return DiffSummaryEntry(key=ld.key, change_type="removed", old_value=ld.old_value)
    return DiffSummaryEntry(
        key=ld.key,
        change_type="changed",
        old_value=ld.old_value,
        new_value=ld.new_value,
    )
