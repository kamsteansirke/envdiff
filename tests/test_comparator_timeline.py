"""Tests for envdiff.comparator_timeline."""
from __future__ import annotations

import pytest

from envdiff.snapshotter import EnvSnapshot
from envdiff.comparator_timeline import build_timeline, TimelineEvent, TimelineResult


def _snap(data: dict[str, str]) -> EnvSnapshot:
    snap = EnvSnapshot.__new__(EnvSnapshot)
    snap._entries = {k: type("E", (), {"value": v, "key": k})() for k, v in data.items()}  # type: ignore[attr-defined]
    snap._data = dict(data)
    return snap


# Minimal duck-type: EnvSnapshot.keys() and .get()
class FakeSnap:
    def __init__(self, data: dict[str, str | None]) -> None:
        self._data = data

    def keys(self) -> list[str]:
        return list(self._data.keys())

    def get(self, key: str) -> str | None:
        return self._data.get(key)


def test_empty_sequence_returns_empty_timeline():
    result = build_timeline([])
    assert result.is_empty()
    assert result.keys_changed() == []


def test_single_snapshot_returns_empty_timeline():
    result = build_timeline([FakeSnap({"A": "1"})])  # type: ignore[arg-type]
    assert result.is_empty()


def test_detects_added_key():
    s1 = FakeSnap({"A": "1"})
    s2 = FakeSnap({"A": "1", "B": "2"})
    result = build_timeline([s1, s2])  # type: ignore[arg-type]
    assert not result.is_empty()
    evs = result.events_for("B")
    assert len(evs) == 1
    assert evs[0].kind == "added"
    assert evs[0].after == "2"
    assert evs[0].before is None


def test_detects_removed_key():
    s1 = FakeSnap({"A": "1", "B": "2"})
    s2 = FakeSnap({"A": "1"})
    result = build_timeline([s1, s2])  # type: ignore[arg-type]
    evs = result.events_for("B")
    assert evs[0].kind == "removed"
    assert evs[0].before == "2"
    assert evs[0].after is None


def test_detects_changed_value():
    s1 = FakeSnap({"A": "old"})
    s2 = FakeSnap({"A": "new"})
    result = build_timeline([s1, s2])  # type: ignore[arg-type]
    evs = result.events_for("A")
    assert evs[0].kind == "changed"
    assert evs[0].before == "old"
    assert evs[0].after == "new"


def test_no_change_produces_no_events():
    s1 = FakeSnap({"A": "1"})
    s2 = FakeSnap({"A": "1"})
    result = build_timeline([s1, s2])  # type: ignore[arg-type]
    assert result.is_empty()


def test_custom_labels_attached_to_events():
    s1 = FakeSnap({"A": "1"})
    s2 = FakeSnap({"A": "2"})
    result = build_timeline([s1, s2], labels=["v1", "v2"])  # type: ignore[arg-type]
    assert result.events[0].snapshot_label == "v2"


def test_keys_changed_returns_sorted_unique_keys():
    s1 = FakeSnap({"B": "1"})
    s2 = FakeSnap({"A": "1", "B": "2"})
    result = build_timeline([s1, s2])  # type: ignore[arg-type]
    assert result.keys_changed() == ["A", "B"]


def test_summary_no_changes():
    result = TimelineResult()
    assert "No changes" in result.summary()


def test_summary_with_events():
    s1 = FakeSnap({"X": "a"})
    s2 = FakeSnap({"X": "b"})
    result = build_timeline([s1, s2])  # type: ignore[arg-type]
    summary = result.summary()
    assert "X" in summary
    assert "1 change" in summary


def test_event_str_added():
    e = TimelineEvent(key="K", kind="added", before=None, after="v", snapshot_label="s2")
    assert str(e) == "[s2] + K"


def test_event_str_removed():
    e = TimelineEvent(key="K", kind="removed", before="v", after=None, snapshot_label="s2")
    assert str(e) == "[s2] - K"


def test_event_str_changed():
    e = TimelineEvent(key="K", kind="changed", before="a", after="b", snapshot_label="s3")
    assert str(e) == "[s3] ~ K"


def test_three_snapshot_chain():
    s1 = FakeSnap({"A": "1"})
    s2 = FakeSnap({"A": "2"})
    s3 = FakeSnap({"A": "3"})
    result = build_timeline([s1, s2, s3])  # type: ignore[arg-type]
    evs = result.events_for("A")
    assert len(evs) == 2
    assert result.labels == ["snap-0", "snap-1", "snap-2"]
