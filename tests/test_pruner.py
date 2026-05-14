"""Tests for envdiff.pruner."""
import pytest
from envdiff.pruner import PruneIssue, PruneResult, prune_env


# ---------------------------------------------------------------------------
# PruneIssue
# ---------------------------------------------------------------------------

def test_issue_str_default_reason():
    issue = PruneIssue(key="OLD_KEY", value="x")
    assert str(issue) == "OLD_KEY: not in reference"


def test_issue_str_custom_reason():
    issue = PruneIssue(key="LEGACY", value="y", reason="deprecated")
    assert str(issue) == "LEGACY: deprecated"


# ---------------------------------------------------------------------------
# PruneResult helpers
# ---------------------------------------------------------------------------

def _make_result(issues=0, kept=2) -> PruneResult:
    r = PruneResult(
        source="test.env",
        issues=[PruneIssue(key=f"BAD_{i}", value="v") for i in range(issues)],
        kept=[f"GOOD_{i}" for i in range(kept)],
    )
    r._original = {f"BAD_{i}": "v" for i in range(issues)}
    r._original.update({f"GOOD_{i}": "v" for i in range(kept)})
    return r


def test_is_clean_when_no_issues():
    assert _make_result(issues=0).is_clean() is True


def test_not_clean_when_issues():
    assert _make_result(issues=1).is_clean() is False


def test_summary_clean():
    r = _make_result(issues=0, kept=3)
    assert "all 3 key(s) are in the reference set" in r.summary()


def test_summary_dirty():
    r = _make_result(issues=2, kept=1)
    assert "2 obsolete key(s) found" in r.summary()
    assert "1 kept" in r.summary()


def test_obsolete_keys_list():
    r = _make_result(issues=2, kept=0)
    assert sorted(r.obsolete_keys()) == ["BAD_0", "BAD_1"]


# ---------------------------------------------------------------------------
# prune_env
# ---------------------------------------------------------------------------

def test_all_keys_in_reference_clean():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = prune_env(env, reference=["HOST", "PORT"], source="prod.env")
    assert result.is_clean()
    assert result.source == "prod.env"
    assert set(result.kept) == {"HOST", "PORT"}


def test_obsolete_key_detected():
    env = {"HOST": "localhost", "OLD_SECRET": "abc"}
    result = prune_env(env, reference=["HOST"])
    assert not result.is_clean()
    assert len(result.issues) == 1
    assert result.issues[0].key == "OLD_SECRET"


def test_empty_env_is_clean():
    result = prune_env({}, reference=["HOST", "PORT"])
    assert result.is_clean()


def test_empty_reference_flags_all():
    env = {"A": "1", "B": "2"}
    result = prune_env(env, reference=[])
    assert len(result.issues) == 2


def test_custom_reason_propagated():
    env = {"DEPRECATED_KEY": "val"}
    result = prune_env(env, reference=[], extra_reason="deprecated")
    assert result.issues[0].reason == "deprecated"


def test_pruned_env_removes_obsolete():
    env = {"HOST": "localhost", "GHOST": "haunt"}
    result = prune_env(env, reference=["HOST"])
    pruned = result.pruned_env()
    assert pruned == {"HOST": "localhost"}
    assert "GHOST" not in pruned


def test_pruned_env_unchanged_when_clean():
    env = {"HOST": "localhost", "PORT": "80"}
    result = prune_env(env, reference=["HOST", "PORT"])
    assert result.pruned_env() == env


def test_kept_keys_are_sorted():
    env = {"Z_KEY": "1", "A_KEY": "2", "M_KEY": "3"}
    result = prune_env(env, reference=["Z_KEY", "A_KEY", "M_KEY"])
    assert result.kept == ["A_KEY", "M_KEY", "Z_KEY"]
