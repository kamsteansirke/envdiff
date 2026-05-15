"""Tests for envdiff.compactor."""
import pytest

from envdiff.compactor import CompactIssue, CompactResult, compact_envs


# ---------------------------------------------------------------------------
# CompactIssue.__str__
# ---------------------------------------------------------------------------

def test_issue_str_redundant():
    issue = CompactIssue(key="PORT", source=".env.staging", kind="redundant",
                         overriding_source=".env.production")
    assert "PORT" in str(issue)
    assert "redundant" in str(issue)


def test_issue_str_overridden():
    issue = CompactIssue(key="DB_URL", source=".env.base", kind="overridden",
                         overriding_source=".env.prod")
    assert "overridden" in str(issue)
    assert ".env.prod" in str(issue)


# ---------------------------------------------------------------------------
# CompactResult helpers
# ---------------------------------------------------------------------------

def _make_result(*kinds: str) -> CompactResult:
    issues = [
        CompactIssue(key=f"KEY_{i}", source="low", kind=k, overriding_source="high")
        for i, k in enumerate(kinds)
    ]
    return CompactResult(issues=issues)


def test_is_clean_when_no_issues():
    assert CompactResult().is_clean is True


def test_not_clean_when_issues():
    result = _make_result("redundant")
    assert result.is_clean is False


def test_summary_clean():
    assert "No redundant" in CompactResult().summary()


def test_summary_lists_counts():
    result = _make_result("redundant", "redundant", "overridden")
    summary = result.summary()
    assert "2 redundant" in summary
    assert "1 overridden" in summary


def test_by_source_groups_correctly():
    issues = [
        CompactIssue(key="A", source="alpha", kind="redundant"),
        CompactIssue(key="B", source="beta", kind="overridden"),
        CompactIssue(key="C", source="alpha", kind="overridden"),
    ]
    result = CompactResult(issues=issues)
    grouped = result.by_source()
    assert len(grouped["alpha"]) == 2
    assert len(grouped["beta"]) == 1


# ---------------------------------------------------------------------------
# compact_envs logic
# ---------------------------------------------------------------------------

def test_no_issues_when_no_overlap():
    high = {"HOST": "prod.example.com"}
    low  = {"PORT": "5432"}
    result = compact_envs([high, low], ["high", "low"])
    assert result.is_clean


def test_redundant_detected_same_value():
    high = {"PORT": "8080"}
    low  = {"PORT": "8080"}  # same value – redundant
    result = compact_envs([high, low], ["high", "low"])
    assert len(result.issues) == 1
    assert result.issues[0].kind == "redundant"
    assert result.issues[0].key == "PORT"
    assert result.issues[0].source == "low"


def test_overridden_detected_different_value():
    high = {"DB": "postgres://prod"}
    low  = {"DB": "postgres://dev"}  # different value – overridden
    result = compact_envs([high, low], ["high", "low"])
    assert len(result.issues) == 1
    assert result.issues[0].kind == "overridden"


def test_highest_priority_layer_never_flagged():
    high = {"A": "1", "B": "2"}
    low  = {"A": "1"}
    result = compact_envs([high, low], ["high", "low"])
    # Only 'low' should have issues, not 'high'
    for issue in result.issues:
        assert issue.source != "high"


def test_three_layers_reports_against_first_match():
    top    = {"X": "top"}
    middle = {"X": "middle"}
    bottom = {"X": "top"}  # matches top, not middle
    result = compact_envs([top, middle, bottom], ["top", "middle", "bottom"])
    bottom_issues = [i for i in result.issues if i.source == "bottom"]
    assert len(bottom_issues) == 1
    assert bottom_issues[0].overriding_source == "top"


def test_mismatched_lengths_raise():
    with pytest.raises(ValueError):
        compact_envs([{"A": "1"}], ["a", "b"])
