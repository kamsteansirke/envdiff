"""Tests for envdiff.rotator."""
from __future__ import annotations

import pytest

from envdiff.rotator import RotationCandidate, RotationResult, rotate_env


# ---------------------------------------------------------------------------
# RotationCandidate
# ---------------------------------------------------------------------------

def test_candidate_str_default_reason():
    c = RotationCandidate(key="API_KEY", old_value="old", new_value="new")
    assert str(c) == "API_KEY: value_changed"


def test_candidate_str_custom_reason():
    c = RotationCandidate(key="DB_PASSWORD", old_value="a", new_value="b", reason="sensitive_rotated")
    assert str(c) == "DB_PASSWORD: sensitive_rotated"


# ---------------------------------------------------------------------------
# RotationResult
# ---------------------------------------------------------------------------

def _make_result(**kwargs):
    defaults = dict(candidates=[], added_keys=[], removed_keys=[])
    defaults.update(kwargs)
    return RotationResult(**defaults)


def test_has_rotations_false_when_empty():
    assert not _make_result().has_rotations


def test_has_rotations_true_when_candidates():
    c = RotationCandidate("K", "a", "b")
    assert _make_result(candidates=[c]).has_rotations


def test_total_changes_sums_all_buckets():
    c = RotationCandidate("K", "a", "b")
    r = _make_result(candidates=[c], added_keys=["X"], removed_keys=["Y", "Z"])
    assert r.total_changes == 4


def test_summary_no_changes():
    assert _make_result().summary() == "no changes detected"


def test_summary_rotated_only():
    c = RotationCandidate("K", "a", "b")
    assert _make_result(candidates=[c]).summary() == "1 rotated"


def test_summary_all_buckets():
    c = RotationCandidate("K", "a", "b")
    r = _make_result(candidates=[c], added_keys=["X", "Y"], removed_keys=["Z"])
    assert r.summary() == "1 rotated, 2 added, 1 removed"


# ---------------------------------------------------------------------------
# rotate_env
# ---------------------------------------------------------------------------

def test_identical_envs_produce_no_changes():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = rotate_env(env, env)
    assert result.total_changes == 0


def test_detects_added_key():
    result = rotate_env({"A": "1"}, {"A": "1", "B": "2"})
    assert result.added_keys == ["B"]
    assert not result.removed_keys


def test_detects_removed_key():
    result = rotate_env({"A": "1", "B": "2"}, {"A": "1"})
    assert result.removed_keys == ["B"]
    assert not result.added_keys


def test_detects_changed_value():
    result = rotate_env({"HOST": "old"}, {"HOST": "new"})
    assert len(result.candidates) == 1
    assert result.candidates[0].key == "HOST"
    assert result.candidates[0].old_value == "old"
    assert result.candidates[0].new_value == "new"


def test_sensitive_key_gets_sensitive_reason():
    result = rotate_env({"DB_PASSWORD": "old"}, {"DB_PASSWORD": "new"})
    assert result.candidates[0].reason == "sensitive_rotated"


def test_non_sensitive_key_gets_value_changed_reason():
    result = rotate_env({"HOST": "a"}, {"HOST": "b"})
    assert result.candidates[0].reason == "value_changed"


def test_sensitive_only_skips_non_sensitive():
    result = rotate_env({"HOST": "a", "API_KEY": "old"}, {"HOST": "b", "API_KEY": "new"}, sensitive_only=True)
    keys = [c.key for c in result.candidates]
    assert "HOST" not in keys
    assert "API_KEY" in keys


def test_added_removed_always_reported_regardless_of_sensitive_only():
    result = rotate_env({"OLD": "v"}, {"NEW": "v"}, sensitive_only=True)
    assert "OLD" in result.removed_keys
    assert "NEW" in result.added_keys
