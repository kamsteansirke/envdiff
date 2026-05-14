"""Tests for envdiff.comparator_chain."""
from __future__ import annotations

import pytest

from envdiff.comparator_chain import ChainResult, compare_chain


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

BASE = {"A": "1", "B": "2", "C": "3"}


def _chain(**targets):
    return compare_chain(BASE, targets, base_name="base")


# ---------------------------------------------------------------------------
# ChainResult unit tests
# ---------------------------------------------------------------------------

def test_chain_result_target_names_sorted():
    result = _chain(z={"A": "1"}, a={"A": "1"})
    assert result.target_names == ["a", "z"]


def test_chain_result_any_differences_false_when_all_match():
    result = _chain(prod=dict(BASE))
    assert not result.any_differences


def test_chain_result_any_differences_true_when_one_differs():
    result = _chain(prod=dict(BASE), staging={"A": "1"})
    assert result.any_differences


def test_diff_for_returns_none_for_unknown_target():
    result = _chain(prod=dict(BASE))
    assert result.diff_for("unknown") is None


def test_diff_for_returns_correct_diff():
    result = _chain(prod=dict(BASE))
    diff = result.diff_for("prod")
    assert diff is not None
    assert not diff.has_differences


# ---------------------------------------------------------------------------
# compare_chain tests
# ---------------------------------------------------------------------------

def test_compare_chain_no_targets_returns_empty():
    result = compare_chain(BASE, {}, base_name="base")
    assert result.target_names == []
    assert not result.any_differences


def test_compare_chain_detects_missing_in_target():
    result = compare_chain(BASE, {"staging": {"A": "1"}}, base_name="base")
    diff = result.diff_for("staging")
    assert "B" in diff.missing_in_target
    assert "C" in diff.missing_in_target


def test_compare_chain_detects_extra_in_target():
    target = dict(BASE)
    target["EXTRA"] = "x"
    result = compare_chain(BASE, {"prod": target}, base_name="base")
    diff = result.diff_for("prod")
    assert "EXTRA" in diff.missing_in_base


def test_compare_chain_detects_mismatch():
    target = dict(BASE)
    target["A"] = "99"
    result = compare_chain(BASE, {"prod": target}, base_name="base")
    diff = result.diff_for("prod")
    assert "A" in diff.mismatched


def test_compare_chain_ignore_values_skips_mismatch():
    target = dict(BASE)
    target["A"] = "99"
    result = compare_chain(BASE, {"prod": target}, base_name="base", ignore_values=True)
    diff = result.diff_for("prod")
    assert not diff.has_differences


def test_compare_chain_summary_ok_label():
    result = compare_chain(BASE, {"prod": dict(BASE)}, base_name="base")
    summary = result.summary()
    assert "OK" in summary
    assert "prod" in summary


def test_compare_chain_summary_shows_counts_when_diff():
    result = compare_chain(BASE, {"staging": {"A": "1"}}, base_name="base")
    summary = result.summary()
    assert "missing" in summary
    assert "staging" in summary
