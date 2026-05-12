"""Tests for envdiff.differ_summary."""
from __future__ import annotations

import pytest

from envdiff.differ import SnapshotDiff
from envdiff.snapshotter import EnvSnapshot, SnapshotEntry
from envdiff.differ_summary import (
    DiffSummaryEntry,
    DiffSummaryReport,
    summarise_diff,
    _line_diff_to_entry,
)
from envdiff.differ import LineDiff


def _snap(pairs: dict) -> EnvSnapshot:
    entries = {k: SnapshotEntry(key=k, value_hash=v) for k, v in pairs.items()}
    return EnvSnapshot(entries=entries)


# ---------------------------------------------------------------------------
# DiffSummaryEntry.__str__
# ---------------------------------------------------------------------------

def test_entry_str_added():
    e = DiffSummaryEntry(key="FOO", change_type="added", new_value="bar")
    assert str(e) == "+ FOO"


def test_entry_str_removed():
    e = DiffSummaryEntry(key="FOO", change_type="removed", old_value="bar")
    assert str(e) == "- FOO"


def test_entry_str_changed():
    e = DiffSummaryEntry(key="FOO", change_type="changed", old_value="a", new_value="b")
    assert "~" in str(e)
    assert "FOO" in str(e)


# ---------------------------------------------------------------------------
# DiffSummaryReport properties
# ---------------------------------------------------------------------------

def test_report_is_empty_when_no_entries():
    r = DiffSummaryReport()
    assert r.is_empty


def test_report_not_empty_with_entry():
    e = DiffSummaryEntry(key="X", change_type="added")
    r = DiffSummaryReport(entries=[e])
    assert not r.is_empty


def test_report_filters_added():
    entries = [
        DiffSummaryEntry(key="A", change_type="added"),
        DiffSummaryEntry(key="B", change_type="removed"),
    ]
    r = DiffSummaryReport(entries=entries)
    assert len(r.added) == 1
    assert r.added[0].key == "A"


def test_report_filters_removed():
    entries = [
        DiffSummaryEntry(key="A", change_type="added"),
        DiffSummaryEntry(key="B", change_type="removed"),
    ]
    r = DiffSummaryReport(entries=entries)
    assert len(r.removed) == 1


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

def test_render_empty_report():
    r = DiffSummaryReport()
    assert r.render() == "No changes detected."


def test_render_includes_summary_line():
    e = DiffSummaryEntry(key="FOO", change_type="added")
    r = DiffSummaryReport(entries=[e])
    out = r.render()
    assert "Summary:" in out
    assert "1 added" in out


def test_render_show_values_includes_arrow():
    e = DiffSummaryEntry(key="FOO", change_type="changed", old_value="x", new_value="y")
    r = DiffSummaryReport(entries=[e])
    out = r.render(show_values=True)
    assert "->" in out


# ---------------------------------------------------------------------------
# summarise_diff
# ---------------------------------------------------------------------------

def test_summarise_diff_empty_snapshots():
    diff = SnapshotDiff(before=_snap({}), after=_snap({}))
    report = summarise_diff(diff)
    assert report.is_empty


def test_summarise_diff_detects_added_key():
    diff = SnapshotDiff(before=_snap({}), after=_snap({"NEW": "hash1"}))
    report = summarise_diff(diff)
    assert len(report.added) == 1
    assert report.added[0].key == "NEW"


def test_summarise_diff_detects_removed_key():
    diff = SnapshotDiff(before=_snap({"OLD": "hash1"}), after=_snap({}))
    report = summarise_diff(diff)
    assert len(report.removed) == 1


def test_summarise_diff_detects_changed_key():
    diff = SnapshotDiff(
        before=_snap({"K": "hash_old"}),
        after=_snap({"K": "hash_new"}),
    )
    report = summarise_diff(diff)
    assert len(report.changed) == 1
    assert report.changed[0].key == "K"
