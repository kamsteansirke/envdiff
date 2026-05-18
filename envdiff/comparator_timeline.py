"""Timeline comparator: track how an env file evolves across multiple snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from envdiff.snapshotter import EnvSnapshot


@dataclass
class TimelineEvent:
    """A single change event between two consecutive snapshots."""

    key: str
    kind: str  # 'added' | 'removed' | 'changed'
    before: Optional[str]
    after: Optional[str]
    snapshot_label: str

    def __str__(self) -> str:
        if self.kind == "added":
            return f"[{self.snapshot_label}] + {self.key}"
        if self.kind == "removed":
            return f"[{self.snapshot_label}] - {self.key}"
        return f"[{self.snapshot_label}] ~ {self.key}"


@dataclass
class TimelineResult:
    """All events across an ordered sequence of snapshots."""

    events: List[TimelineEvent] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.events) == 0

    def events_for(self, key: str) -> List[TimelineEvent]:
        return [e for e in self.events if e.key == key]

    def keys_changed(self) -> List[str]:
        seen: Dict[str, None] = {}
        for e in self.events:
            seen[e.key] = None
        return sorted(seen)

    def summary(self) -> str:
        if self.is_empty():
            return "No changes across timeline."
        lines = [f"{len(self.labels)} snapshot(s), {len(self.events)} event(s):"]
        for key in self.keys_changed():
            evs = self.events_for(key)
            lines.append(f"  {key}: {len(evs)} change(s)")
        return "\n".join(lines)


def build_timeline(
    snapshots: Sequence[EnvSnapshot],
    labels: Optional[Sequence[str]] = None,
) -> TimelineResult:
    """Compare consecutive snapshots and collect change events."""
    if labels is None:
        labels = [f"snap-{i}" for i in range(len(snapshots))]

    result = TimelineResult(labels=list(labels))

    for i in range(1, len(snapshots)):
        prev = snapshots[i - 1]
        curr = snapshots[i]
        label = labels[i]

        prev_keys = set(prev.keys())
        curr_keys = set(curr.keys())

        for key in sorted(curr_keys - prev_keys):
            result.events.append(
                TimelineEvent(key=key, kind="added", before=None,
                               after=curr.get(key), snapshot_label=label)
            )
        for key in sorted(prev_keys - curr_keys):
            result.events.append(
                TimelineEvent(key=key, kind="removed", before=prev.get(key),
                               after=None, snapshot_label=label)
            )
        for key in sorted(prev_keys & curr_keys):
            pv, cv = prev.get(key), curr.get(key)
            if pv != cv:
                result.events.append(
                    TimelineEvent(key=key, kind="changed", before=pv,
                                   after=cv, snapshot_label=label)
                )

    return result
