"""Tests for envdiff.comparator."""

import pytest

from envdiff.comparator import EnvDiff, compare_envs


BASE = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "abc123"}
TARGET_SAME = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "abc123"}
TARGET_MISSING = {"DB_HOST": "localhost", "DB_PORT": "5432"}
TARGET_EXTRA = {**BASE, "NEW_KEY": "value"}
TARGET_MISMATCH = {"DB_HOST": "prod-host", "DB_PORT": "5432", "SECRET_KEY": "abc123"}


def test_no_differences():
    diff = compare_envs(BASE, TARGET_SAME)
    assert not diff.has_differences


def test_missing_in_target():
    diff = compare_envs(BASE, TARGET_MISSING)
    assert "SECRET_KEY" in diff.missing_in_target
    assert diff.has_differences


def test_missing_in_base():
    diff = compare_envs(BASE, TARGET_EXTRA)
    assert "NEW_KEY" in diff.missing_in_base
    assert diff.has_differences


def test_mismatched_values():
    diff = compare_envs(BASE, TARGET_MISMATCH)
    assert "DB_HOST" in diff.mismatched
    assert diff.mismatched["DB_HOST"] == {"base": "localhost", "target": "prod-host"}


def test_ignore_values_skips_mismatch():
    diff = compare_envs(BASE, TARGET_MISMATCH, ignore_values=True)
    assert not diff.mismatched
    assert not diff.has_differences


def test_custom_names():
    diff = compare_envs(BASE, TARGET_MISSING, base_name=".env", target_name=".env.prod")
    assert diff.base_name == ".env"
    assert diff.target_name == ".env.prod"


def test_summary_no_diff():
    diff = compare_envs(BASE, TARGET_SAME, base_name="a", target_name="b")
    summary = diff.summary()
    assert "No differences" in summary


def test_summary_with_missing():
    diff = compare_envs(BASE, TARGET_MISSING, base_name="a", target_name="b")
    summary = diff.summary()
    assert "SECRET_KEY" in summary
    assert "Missing in b" in summary


def test_summary_with_mismatch():
    diff = compare_envs(BASE, TARGET_MISMATCH, base_name="a", target_name="b")
    summary = diff.summary()
    assert "DB_HOST" in summary
    assert "Mismatched" in summary


def test_none_values():
    base = {"KEY": None}
    target = {"KEY": "value"}
    diff = compare_envs(base, target)
    assert "KEY" in diff.mismatched
    assert diff.mismatched["KEY"] == {"base": None, "target": "value"}
