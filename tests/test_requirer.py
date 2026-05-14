"""Tests for envdiff.requirer."""
from __future__ import annotations

import pytest

from envdiff.requirer import RequireIssue, RequireResult, require_keys


# ---------------------------------------------------------------------------
# RequireIssue
# ---------------------------------------------------------------------------

def test_issue_str_default_reason():
    issue = RequireIssue(key="DATABASE_URL")
    assert str(issue) == "DATABASE_URL: missing required key"


def test_issue_str_custom_reason():
    issue = RequireIssue(key="SECRET", reason="required key has empty value")
    assert str(issue) == "SECRET: required key has empty value"


# ---------------------------------------------------------------------------
# RequireResult helpers
# ---------------------------------------------------------------------------

def _make_result(issues=None, source="test.env"):
    return RequireResult(source=source, issues=issues or [])


def test_is_clean_when_no_issues():
    assert _make_result().is_clean() is True


def test_not_clean_when_issues():
    result = _make_result(issues=[RequireIssue(key="FOO")])
    assert result.is_clean() is False


def test_missing_keys_empty():
    assert _make_result().missing_keys() == []


def test_missing_keys_lists_keys():
    result = _make_result(issues=[RequireIssue(key="A"), RequireIssue(key="B")])
    assert result.missing_keys() == ["A", "B"]


def test_summary_clean():
    result = _make_result(source="prod.env")
    assert result.summary() == "prod.env: all required keys present"


def test_summary_with_issues():
    result = _make_result(
        issues=[RequireIssue(key="FOO"), RequireIssue(key="BAR")],
        source="prod.env",
    )
    summary = result.summary()
    assert "2 missing required key(s)" in summary
    assert "FOO" in summary
    assert "BAR" in summary


# ---------------------------------------------------------------------------
# require_keys
# ---------------------------------------------------------------------------

def test_all_present_returns_clean():
    env = {"A": "1", "B": "2", "C": "3"}
    result = require_keys(env, ["A", "B"], source="x.env")
    assert result.is_clean()
    assert result.source == "x.env"


def test_missing_key_detected():
    env = {"A": "1"}
    result = require_keys(env, ["A", "MISSING"])
    assert not result.is_clean()
    assert "MISSING" in result.missing_keys()


def test_multiple_missing_keys():
    env = {}
    result = require_keys(env, ["X", "Y", "Z"])
    assert result.missing_keys() == ["X", "Y", "Z"]


def test_empty_required_list_is_clean():
    result = require_keys({"A": "1"}, [])
    assert result.is_clean()


def test_allow_empty_true_accepts_empty_value():
    env = {"KEY": ""}
    result = require_keys(env, ["KEY"], allow_empty=True)
    assert result.is_clean()


def test_allow_empty_false_rejects_empty_value():
    env = {"KEY": ""}
    result = require_keys(env, ["KEY"], allow_empty=False)
    assert not result.is_clean()
    assert result.issues[0].reason == "required key has empty value"


def test_allow_empty_false_accepts_nonempty_value():
    env = {"KEY": "somevalue"}
    result = require_keys(env, ["KEY"], allow_empty=False)
    assert result.is_clean()


def test_default_source_label():
    result = require_keys({}, [])
    assert result.source == "<env>"
