"""Tests for envdiff.pivot."""
from __future__ import annotations

import pytest

from envdiff.pivot import PivotRow, PivotTable, pivot_envs


# ---------------------------------------------------------------------------
# PivotRow
# ---------------------------------------------------------------------------

class TestPivotRow:
    def _row(self, **values):
        return PivotRow(key="KEY", values=values)

    def test_present_in_returns_envs_with_value(self):
        row = self._row(dev="1", prod=None, staging="1")
        assert sorted(row.present_in()) == ["dev", "staging"]

    def test_absent_in_returns_envs_without_value(self):
        row = self._row(dev="1", prod=None)
        assert row.absent_in() == ["prod"]

    def test_is_consistent_all_same(self):
        row = self._row(dev="hello", prod="hello")
        assert row.is_consistent() is True

    def test_is_consistent_ignores_absent(self):
        row = self._row(dev="hello", prod=None)
        assert row.is_consistent() is True

    def test_is_consistent_false_on_mismatch(self):
        row = self._row(dev="hello", prod="world")
        assert row.is_consistent() is False

    def test_is_universal_all_present(self):
        row = self._row(dev="a", prod="b")
        assert row.is_universal() is True

    def test_is_universal_false_when_absent(self):
        row = self._row(dev="a", prod=None)
        assert row.is_universal() is False


# ---------------------------------------------------------------------------
# pivot_envs
# ---------------------------------------------------------------------------

def test_empty_envs_returns_empty_table():
    table = pivot_envs({})
    assert table.rows == []
    assert table.env_names == []


def test_single_env_all_keys_present():
    table = pivot_envs({"dev": {"A": "1", "B": "2"}})
    assert len(table.rows) == 2
    for row in table.rows:
        assert row.values["dev"] is not None


def test_keys_sorted_alphabetically():
    table = pivot_envs({"dev": {"Z": "z", "A": "a", "M": "m"}})
    assert [r.key for r in table.rows] == ["A", "M", "Z"]


def test_missing_key_recorded_as_none():
    table = pivot_envs({"dev": {"A": "1"}, "prod": {"B": "2"}})
    row_a = next(r for r in table.rows if r.key == "A")
    assert row_a.values["dev"] == "1"
    assert row_a.values["prod"] is None


def test_missing_rows_filters_correctly():
    table = pivot_envs({"dev": {"A": "1", "B": "2"}, "prod": {"A": "1"}})
    missing = table.missing_rows()
    assert len(missing) == 1
    assert missing[0].key == "B"


def test_inconsistent_rows_filters_correctly():
    table = pivot_envs({"dev": {"A": "1"}, "prod": {"A": "2"}})
    bad = table.inconsistent_rows()
    assert len(bad) == 1
    assert bad[0].key == "A"


def test_summary_contains_counts():
    table = pivot_envs({"dev": {"A": "1", "B": "2"}, "prod": {"A": "9"}})
    s = table.summary()
    assert "2 keys" in s
    assert "2 environments" in s


def test_all_keys_returns_list():
    table = pivot_envs({"dev": {"X": "1", "Y": "2"}})
    assert set(table.all_keys()) == {"X", "Y"}
