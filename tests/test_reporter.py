"""Tests for envdiff.reporter."""

import pytest
from envdiff.comparator import compare_envs
from envdiff.reporter import format_diff, format_many, ReportOptions


BASE = {"KEY_A": "val_a", "KEY_B": "val_b", "SHARED": "same"}
TARGET_OK = {"KEY_A": "val_a", "KEY_B": "val_b", "SHARED": "same"}
TARGET_MISSING = {"KEY_A": "val_a", "SHARED": "same"}
TARGET_EXTRA = {"KEY_A": "val_a", "KEY_B": "val_b", "SHARED": "same", "EXTRA": "x"}
TARGET_MISMATCH = {"KEY_A": "val_a", "KEY_B": "CHANGED", "SHARED": "same"}

NO_COLOR = ReportOptions(color=False)


def test_format_diff_no_differences():
    diff = compare_envs(BASE, TARGET_OK, "prod.env")
    output = format_diff(diff, NO_COLOR)
    assert "No differences found" in output


def test_format_diff_missing_in_target():
    diff = compare_envs(BASE, TARGET_MISSING, "prod.env")
    output = format_diff(diff, NO_COLOR)
    assert "MISSING" in output
    assert "KEY_B" in output


def test_format_diff_extra_in_target():
    diff = compare_envs(BASE, TARGET_EXTRA, "prod.env")
    output = format_diff(diff, NO_COLOR)
    assert "EXTRA" in output
    assert "EXTRA" in output


def test_format_diff_mismatch():
    diff = compare_envs(BASE, TARGET_MISMATCH, "prod.env")
    output = format_diff(diff, NO_COLOR)
    assert "MISMATCH" in output
    assert "KEY_B" in output


def test_format_diff_show_values():
    opts = ReportOptions(color=False, show_values=True)
    diff = compare_envs(BASE, TARGET_MISMATCH, "prod.env")
    output = format_diff(diff, opts)
    assert "val_b" in output
    assert "CHANGED" in output


def test_format_diff_hide_values_by_default():
    diff = compare_envs(BASE, TARGET_MISMATCH, "prod.env")
    output = format_diff(diff, NO_COLOR)
    assert "val_b" not in output
    assert "CHANGED" not in output


def test_format_diff_includes_target_name():
    diff = compare_envs(BASE, TARGET_MISSING, "staging.env")
    output = format_diff(diff, NO_COLOR)
    assert "staging.env" in output


def test_format_many_empty():
    output = format_many([], NO_COLOR)
    assert "No comparisons" in output


def test_format_many_multiple():
    d1 = compare_envs(BASE, TARGET_MISSING, "staging.env")
    d2 = compare_envs(BASE, TARGET_MISMATCH, "prod.env")
    output = format_many([d1, d2], NO_COLOR)
    assert "staging.env" in output
    assert "prod.env" in output


def test_format_diff_color_codes_present_by_default():
    diff = compare_envs(BASE, TARGET_MISSING, "prod.env")
    output = format_diff(diff)  # color=True by default
    assert "\033[" in output
