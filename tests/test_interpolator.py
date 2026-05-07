"""Tests for envdiff.interpolator."""
import pytest
from envdiff.interpolator import (
    InterpolationIssue,
    InterpolationResult,
    _find_refs,
    interpolate_env,
)


# ---------------------------------------------------------------------------
# _find_refs
# ---------------------------------------------------------------------------

def test_find_refs_dollar_brace():
    assert _find_refs("${FOO}") == ["FOO"]


def test_find_refs_bare_dollar():
    assert _find_refs("$BAR") == ["BAR"]


def test_find_refs_multiple():
    refs = _find_refs("${HOST}:${PORT}")
    assert refs == ["HOST", "PORT"]


def test_find_refs_no_refs():
    assert _find_refs("plain-value") == []


def test_find_refs_mixed():
    refs = _find_refs("$PROTO://${HOST}")
    assert "PROTO" in refs
    assert "HOST" in refs


# ---------------------------------------------------------------------------
# interpolate_env — happy paths
# ---------------------------------------------------------------------------

def test_no_refs_returns_unchanged():
    env = {"KEY": "value", "NUM": "42"}
    result = interpolate_env(env)
    assert result.is_clean
    assert result.resolved == env


def test_resolves_self_reference():
    env = {"HOST": "localhost", "URL": "http://${HOST}/api"}
    result = interpolate_env(env)
    assert result.is_clean
    assert result.resolved["URL"] == "http://localhost/api"


def test_resolves_bare_dollar():
    env = {"PROTO": "https", "BASE": "$PROTO://example.com"}
    result = interpolate_env(env)
    assert result.is_clean
    assert result.resolved["BASE"] == "https://example.com"


def test_resolves_from_external():
    env = {"URL": "http://${HOSTNAME}/path"}
    external = {"HOSTNAME": "prod.example.com"}
    result = interpolate_env(env, external=external)
    assert result.is_clean
    assert result.resolved["URL"] == "http://prod.example.com/path"


def test_env_overrides_external():
    env = {"HOST": "override", "URL": "${HOST}"}
    external = {"HOST": "external-value"}
    result = interpolate_env(env, external=external)
    assert result.resolved["URL"] == "override"


# ---------------------------------------------------------------------------
# interpolate_env — missing references
# ---------------------------------------------------------------------------

def test_unresolved_ref_creates_issue():
    env = {"URL": "http://${MISSING_HOST}/api"}
    result = interpolate_env(env)
    assert not result.is_clean
    assert len(result.issues) == 1
    assert result.issues[0].key == "URL"
    assert result.issues[0].ref == "MISSING_HOST"


def test_unresolved_refs_recorded():
    env = {"CONN": "${DB_HOST}:${DB_PORT}"}
    result = interpolate_env(env)
    assert "CONN" in result.unresolved_refs
    assert set(result.unresolved_refs["CONN"]) == {"DB_HOST", "DB_PORT"}


def test_summary_clean():
    result = interpolate_env({"A": "1"})
    assert "cleanly" in result.summary()


def test_summary_with_issues():
    env = {"X": "${UNDEFINED}"}
    result = interpolate_env(env)
    summary = result.summary()
    assert "1 interpolation issue" in summary
    assert "UNDEFINED" in summary


def test_issue_str():
    issue = InterpolationIssue(key="K", ref="V", message="unresolved reference '$V'")
    assert "K" in str(issue)
    assert "$V" in str(issue)
