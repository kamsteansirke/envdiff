"""Tests for envdiff.deprecator."""
import pytest
from envdiff.deprecator import (
    DeprecationIssue,
    DeprecationResult,
    check_deprecations,
)


# ---------------------------------------------------------------------------
# DeprecationIssue.__str__
# ---------------------------------------------------------------------------

def test_issue_str_no_replacement():
    issue = DeprecationIssue(key="OLD_KEY", reason="Removed in v2")
    assert str(issue) == "OLD_KEY: Removed in v2"


def test_issue_str_with_replacement():
    issue = DeprecationIssue(key="OLD_KEY", reason="Renamed", replacement="NEW_KEY")
    assert str(issue) == "OLD_KEY: Renamed (use 'NEW_KEY' instead)"


# ---------------------------------------------------------------------------
# DeprecationResult helpers
# ---------------------------------------------------------------------------

def _make_result(*keys: str) -> DeprecationResult:
    issues = [DeprecationIssue(key=k, reason="Deprecated") for k in keys]
    return DeprecationResult(issues=issues)


def test_is_clean_when_no_issues():
    assert DeprecationResult().is_clean() is True


def test_not_clean_when_issues():
    assert _make_result("OLD").is_clean() is False


def test_keys_sorted():
    result = _make_result("ZEBRA", "ALPHA", "MIDDLE")
    assert result.keys() == ["ALPHA", "MIDDLE", "ZEBRA"]


def test_summary_clean():
    assert DeprecationResult().summary() == "No deprecated keys found."


def test_summary_with_issues():
    result = _make_result("OLD_KEY")
    summary = result.summary()
    assert "1 deprecated" in summary
    assert "OLD_KEY" in summary


# ---------------------------------------------------------------------------
# check_deprecations
# ---------------------------------------------------------------------------

REGISTRY = {
    "OLD_API_KEY": {"reason": "Renamed", "replacement": "API_KEY"},
    "LEGACY_MODE": {"reason": "Feature removed"},
}


def test_clean_env_returns_no_issues():
    env = {"API_KEY": "abc", "DEBUG": "true"}
    result = check_deprecations(env, REGISTRY)
    assert result.is_clean()


def test_deprecated_key_detected():
    env = {"OLD_API_KEY": "secret", "DEBUG": "true"}
    result = check_deprecations(env, REGISTRY)
    assert not result.is_clean()
    assert "OLD_API_KEY" in result.keys()


def test_replacement_propagated():
    env = {"OLD_API_KEY": "secret"}
    result = check_deprecations(env, REGISTRY)
    issue = result.issues[0]
    assert issue.replacement == "API_KEY"


def test_reason_propagated():
    env = {"LEGACY_MODE": "1"}
    result = check_deprecations(env, REGISTRY)
    issue = result.issues[0]
    assert issue.reason == "Feature removed"
    assert issue.replacement is None


def test_multiple_deprecated_keys():
    env = {"OLD_API_KEY": "x", "LEGACY_MODE": "1", "KEEP": "y"}
    result = check_deprecations(env, REGISTRY)
    assert len(result.issues) == 2
    assert set(result.keys()) == {"OLD_API_KEY", "LEGACY_MODE"}


def test_empty_env_is_clean():
    result = check_deprecations({}, REGISTRY)
    assert result.is_clean()


def test_empty_registry_is_clean():
    env = {"OLD_API_KEY": "x", "LEGACY_MODE": "1"}
    result = check_deprecations(env, {})
    assert result.is_clean()
