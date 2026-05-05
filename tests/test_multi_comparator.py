"""Tests for envdiff.multi_comparator."""

import pytest
from pathlib import Path

from envdiff.multi_comparator import compare_many, full_summary


@pytest.fixture
def env_dir(tmp_path):
    base = tmp_path / ".env"
    base.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET=base_secret\n")

    prod = tmp_path / ".env.prod"
    prod.write_text("DB_HOST=prod-host\nDB_PORT=5432\nSECRET=prod_secret\n")

    staging = tmp_path / ".env.staging"
    staging.write_text("DB_HOST=staging-host\nDB_PORT=5432\n")

    return tmp_path


def test_compare_many_returns_one_diff_per_target(env_dir):
    base = env_dir / ".env"
    targets = [env_dir / ".env.prod", env_dir / ".env.staging"]
    diffs = compare_many(base, targets)
    assert len(diffs) == 2


def test_compare_many_diff_names(env_dir):
    base = env_dir / ".env"
    targets = [env_dir / ".env.prod"]
    diffs = compare_many(base, targets)
    assert diffs[0].base_name == ".env"
    assert diffs[0].target_name == ".env.prod"


def test_compare_many_detects_mismatch(env_dir):
    base = env_dir / ".env"
    targets = [env_dir / ".env.prod"]
    diffs = compare_many(base, targets)
    assert "DB_HOST" in diffs[0].mismatched


def test_compare_many_detects_missing(env_dir):
    base = env_dir / ".env"
    targets = [env_dir / ".env.staging"]
    diffs = compare_many(base, targets)
    assert "SECRET" in diffs[0].missing_in_target


def test_compare_many_ignore_values(env_dir):
    base = env_dir / ".env"
    targets = [env_dir / ".env.prod"]
    diffs = compare_many(base, targets, ignore_values=True)
    assert not diffs[0].mismatched


def test_full_summary_empty():
    result = full_summary([])
    assert "No comparisons" in result


def test_full_summary_contains_all_targets(env_dir):
    base = env_dir / ".env"
    targets = [env_dir / ".env.prod", env_dir / ".env.staging"]
    diffs = compare_many(base, targets)
    summary = full_summary(diffs)
    assert ".env.prod" in summary
    assert ".env.staging" in summary
