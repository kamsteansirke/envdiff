"""Tests for envdiff.exporter."""

from __future__ import annotations

import json

import pytest

from envdiff.comparator import compare_envs
from envdiff.exporter import ExportOptions, export_diff, export_many


BASE = {"APP_ENV": "production", "DB_HOST": "localhost", "SECRET": "abc"}
TARGET = {"APP_ENV": "staging", "DB_HOST": "localhost"}


@pytest.fixture()
def diff():
    return compare_envs(BASE, TARGET, base_name=".env", target_name=".env.staging")


# --- JSON ---

def test_export_json_structure(diff):
    result = export_diff(diff, ExportOptions(fmt="json"))
    data = json.loads(result)
    assert isinstance(data, list)
    statuses = {row["status"] for row in data}
    assert "mismatch" in statuses
    assert "missing_in_target" in statuses


def test_export_json_no_values_by_default(diff):
    result = export_diff(diff, ExportOptions(fmt="json"))
    data = json.loads(result)
    for row in data:
        assert "base_value" not in row
        assert "target_value" not in row


def test_export_json_show_values(diff):
    result = export_diff(diff, ExportOptions(fmt="json", show_values=True))
    data = json.loads(result)
    mismatch = next(r for r in data if r["status"] == "mismatch")
    assert mismatch["base_value"] == "production"
    assert mismatch["target_value"] == "staging"


def test_export_json_empty():
    d = compare_envs({"A": "1"}, {"A": "1"}, base_name="a", target_name="b")
    result = export_diff(d, ExportOptions(fmt="json"))
    assert json.loads(result) == []


# --- CSV ---

def test_export_csv_has_header(diff):
    result = export_diff(diff, ExportOptions(fmt="csv"))
    first_line = result.splitlines()[0]
    assert "key" in first_line
    assert "status" in first_line


def test_export_csv_rows(diff):
    result = export_diff(diff, ExportOptions(fmt="csv"))
    lines = result.strip().splitlines()
    # header + at least 2 data rows (mismatch + missing)
    assert len(lines) >= 3


def test_export_csv_empty():
    d = compare_envs({"A": "1"}, {"A": "1"}, base_name="a", target_name="b")
    result = export_diff(d, ExportOptions(fmt="csv"))
    assert result == ""


# --- Markdown ---

def test_export_markdown_has_table(diff):
    result = export_diff(diff, ExportOptions(fmt="markdown"))
    assert "|" in result
    assert "---" in result


def test_export_markdown_empty():
    d = compare_envs({"A": "1"}, {"A": "1"}, base_name="a", target_name="b")
    result = export_diff(d, ExportOptions(fmt="markdown"))
    assert "No differences" in result


# --- export_many ---

def test_export_many_combines_rows():
    d1 = compare_envs({"X": "1"}, {}, base_name="a", target_name="b")
    d2 = compare_envs({"Y": "2"}, {}, base_name="a", target_name="c")
    result = export_many([d1, d2], ExportOptions(fmt="json"))
    data = json.loads(result)
    keys = {r["key"] for r in data}
    assert "X" in keys
    assert "Y" in keys


def test_export_invalid_format(diff):
    with pytest.raises(ValueError, match="Unsupported"):
        from envdiff.exporter import _render
        _render([], "xml")  # type: ignore[arg-type]
