"""Tests for envdiff.staler."""
from __future__ import annotations

import pytest

from envdiff.staler import StaleIssue, StaleResult, check_staleness, _detect_placeholder


# ---------------------------------------------------------------------------
# _detect_placeholder
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [
    "changeme",
    "CHANGEME",
    "change_me",
    "replace_me",
    "<YOUR_SECRET>",
    "${UNRESOLVED}",
    "[fill this in]",
    "example.com",
    "localhost",
    "0.0.0.0",
    "none",
    "null",
    "undefined",
    "n/a",
    "todo",
    "placeholder",
    "your_key_here",
])
def test_placeholder_detected(value):
    assert _detect_placeholder(value) is not None


@pytest.mark.parametrize("value", [
    "supersecretpassword",
    "postgres://user:pass@db:5432/mydb",
    "production.myapp.com",
    "true",
    "8080",
    "us-east-1",
])
def test_real_value_not_flagged(value):
    assert _detect_placeholder(value) is None


# ---------------------------------------------------------------------------
# check_staleness
# ---------------------------------------------------------------------------

def test_empty_env_is_clean():
    result = check_staleness({})
    assert result.is_clean


def test_clean_env_is_clean():
    result = check_staleness({"DB_HOST": "db.prod.internal", "PORT": "5432"})
    assert result.is_clean


def test_stale_value_detected():
    result = check_staleness({"API_KEY": "changeme"})
    assert not result.is_clean
    assert len(result.issues) == 1
    assert result.issues[0].key == "API_KEY"


def test_multiple_stale_values():
    env = {
        "A": "changeme",
        "B": "<YOUR_TOKEN>",
        "C": "real_value",
    }
    result = check_staleness(env)
    keys = {i.key for i in result.issues}
    assert keys == {"A", "B"}


# ---------------------------------------------------------------------------
# StaleResult helpers
# ---------------------------------------------------------------------------

def test_summary_clean():
    r = StaleResult()
    assert "No stale" in r.summary()


def test_summary_with_issues():
    r = StaleResult(issues=[StaleIssue(key="X", value="todo", reason="matches pattern")])
    text = r.summary()
    assert "1 stale" in text
    assert "X" in text


def test_stale_issue_str():
    issue = StaleIssue(key="FOO", value="changeme", reason="placeholder")
    assert "FOO" in str(issue)
    assert "changeme" in str(issue)
    assert "placeholder" in str(issue)
