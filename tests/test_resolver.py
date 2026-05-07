"""Tests for envdiff.resolver."""
from envdiff.resolver import ResolveIssue, ResolveResult, _find_refs, resolve_env


# ---------------------------------------------------------------------------
# _find_refs
# ---------------------------------------------------------------------------

def test_find_refs_brace_syntax():
    assert _find_refs("${FOO}") == ["FOO"]


def test_find_refs_bare_syntax():
    assert _find_refs("$BAR") == ["BAR"]


def test_find_refs_mixed():
    refs = _find_refs("${A}/$B")
    assert refs == ["A", "B"]


def test_find_refs_none():
    assert _find_refs("plain value") == []


# ---------------------------------------------------------------------------
# resolve_env — happy path
# ---------------------------------------------------------------------------

def test_no_references_unchanged():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = resolve_env(env)
    assert result.is_clean()
    assert result.resolved == env


def test_simple_reference_resolved():
    env = {"BASE": "http://localhost", "URL": "${BASE}/api"}
    result = resolve_env(env)
    assert result.is_clean()
    assert result.resolved["URL"] == "http://localhost/api"


def test_chained_references_resolved():
    env = {"A": "hello", "B": "${A} world", "C": "${B}!"}
    result = resolve_env(env)
    assert result.is_clean()
    assert result.resolved["C"] == "hello world!"


def test_bare_dollar_reference_resolved():
    env = {"NAME": "envdiff", "GREETING": "Hello $NAME"}
    result = resolve_env(env)
    assert result.resolved["GREETING"] == "Hello envdiff"


# ---------------------------------------------------------------------------
# resolve_env — issues
# ---------------------------------------------------------------------------

def test_missing_reference_records_issue():
    env = {"URL": "${MISSING}/path"}
    result = resolve_env(env)
    assert not result.is_clean()
    assert len(result.issues) == 1
    assert result.issues[0].key == "URL"
    assert result.issues[0].ref == "MISSING"
    assert result.issues[0].reason == "missing"


def test_allow_missing_suppresses_issue():
    env = {"URL": "${MISSING}/path"}
    result = resolve_env(env, allow_missing=True)
    assert result.is_clean()


def test_circular_reference_records_issue():
    env = {"A": "${B}", "B": "${A}"}
    result = resolve_env(env)
    assert not result.is_clean()
    reasons = {i.reason for i in result.issues}
    assert "circular" in reasons


def test_self_reference_records_circular():
    env = {"X": "${X}"}
    result = resolve_env(env)
    assert not result.is_clean()
    assert result.issues[0].reason == "circular"


# ---------------------------------------------------------------------------
# ResolveIssue / ResolveResult helpers
# ---------------------------------------------------------------------------

def test_issue_str():
    issue = ResolveIssue(key="URL", ref="HOST", reason="missing")
    assert "URL" in str(issue)
    assert "HOST" in str(issue)
    assert "missing" in str(issue)


def test_summary_clean():
    result = ResolveResult(resolved={"A": "1", "B": "2"})
    assert "2 keys" in result.summary()


def test_summary_with_issues():
    issue = ResolveIssue(key="URL", ref="MISSING", reason="missing")
    result = ResolveResult(resolved={"URL": ""}, issues=[issue])
    summary = result.summary()
    assert "1 resolution issue" in summary
    assert "URL" in summary
