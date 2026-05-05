"""Tests for envdiff.differ."""

import pytest

from envdiff.differ import LineDiff, SnapshotDiff, diff_snapshots


BEFORE = {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}
AFTER = {"HOST": "prod.example.com", "PORT": "5432", "SECRET": "abc123"}


def test_empty_snapshots_produce_no_diff():
    result = diff_snapshots({}, {})
    assert result.is_empty
    assert result.all_changes == []


def test_identical_snapshots_produce_no_diff():
    result = diff_snapshots(BEFORE, BEFORE)
    assert result.is_empty


def test_detects_added_key():
    result = diff_snapshots(BEFORE, AFTER)
    keys = [d.key for d in result.added]
    assert "SECRET" in keys


def test_detects_removed_key():
    result = diff_snapshots(BEFORE, AFTER)
    keys = [d.key for d in result.removed]
    assert "DEBUG" in keys


def test_detects_changed_value():
    result = diff_snapshots(BEFORE, AFTER)
    keys = [d.key for d in result.changed]
    assert "HOST" in keys


def test_unchanged_key_not_in_diff():
    result = diff_snapshots(BEFORE, AFTER)
    all_keys = [d.key for d in result.all_changes]
    assert "PORT" not in all_keys


def test_all_changes_ordering():
    """all_changes returns removed, then added, then changed."""
    result = diff_snapshots(BEFORE, AFTER)
    statuses = [d.status for d in result.all_changes]
    # removed comes before added, added before changed
    assert statuses.index("removed") < statuses.index("added")


def test_line_diff_str_added():
    d = LineDiff(key="FOO", status="added", new_value="bar")
    assert str(d) == "+ FOO=bar"


def test_line_diff_str_removed():
    d = LineDiff(key="FOO", status="removed", old_value="bar")
    assert str(d) == "- FOO=bar"


def test_line_diff_str_changed():
    d = LineDiff(key="FOO", status="changed", old_value="old", new_value="new")
    assert "~" in str(d)
    assert "old" in str(d)
    assert "new" in str(d)


def test_snapshot_diff_is_empty_false_when_changes_present():
    result = diff_snapshots({"A": "1"}, {"A": "2"})
    assert not result.is_empty


def test_added_value_captured():
    result = diff_snapshots({}, {"NEW_KEY": "hello"})
    assert result.added[0].new_value == "hello"
    assert result.added[0].old_value is None


def test_removed_value_captured():
    result = diff_snapshots({"OLD_KEY": "bye"}, {})
    assert result.removed[0].old_value == "bye"
    assert result.removed[0].new_value is None
