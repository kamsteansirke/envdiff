"""Tests for envdiff.scorer."""
import pytest

from envdiff.comparator import EnvDiff
from envdiff.linter import LintResult, LintIssue
from envdiff.auditor import AuditResult, AuditViolation
from envdiff.scorer import score_env, HealthScore, ScoreBreakdown


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_diff(missing=(), extra=(), mismatched=()) -> EnvDiff:
    return EnvDiff(
        base_name="base",
        target_name="target",
        missing_in_target=list(missing),
        missing_in_base=list(extra),
        mismatched=dict(mismatched),
    )


def _make_lint(*codes) -> LintResult:
    issues = [LintIssue(line=1, code=c, message="x") for c in codes]
    return LintResult(issues=issues)


def _make_audit(*messages) -> AuditResult:
    violations = [AuditViolation(key="K", message=m) for m in messages]
    return AuditResult(violations=violations)


# ---------------------------------------------------------------------------
# perfect score
# ---------------------------------------------------------------------------

def test_perfect_score_no_inputs():
    hs = score_env()
    assert hs.score == 100
    assert hs.grade == "A"
    assert hs.notes == []


def test_perfect_score_clean_diff():
    hs = score_env(diff=_make_diff())
    assert hs.score == 100
    assert hs.grade == "A"


# ---------------------------------------------------------------------------
# diff penalties
# ---------------------------------------------------------------------------

def test_missing_key_reduces_score():
    hs = score_env(diff=_make_diff(missing=["FOO"]))
    assert hs.score == 90  # 100 - 10
    assert hs.breakdown.missing_keys == 1
    assert any("missing" in n for n in hs.notes)


def test_extra_key_reduces_score():
    hs = score_env(diff=_make_diff(extra=["BAR"]))
    assert hs.score == 95  # 100 - 5


def test_mismatch_reduces_score():
    hs = score_env(diff=_make_diff(mismatched=[("X", ("a", "b"))]))
    assert hs.score == 93  # 100 - 7


# ---------------------------------------------------------------------------
# lint penalties
# ---------------------------------------------------------------------------

def test_lint_error_reduces_score():
    hs = score_env(lint=_make_lint("E001"))
    assert hs.score == 92  # 100 - 8
    assert hs.breakdown.lint_errors == 1


def test_lint_warning_reduces_score():
    hs = score_env(lint=_make_lint("W002"))
    assert hs.score == 97  # 100 - 3
    assert hs.breakdown.lint_warnings == 1


# ---------------------------------------------------------------------------
# audit penalties
# ---------------------------------------------------------------------------

def test_audit_violation_reduces_score():
    hs = score_env(audit=_make_audit("bad value"))
    assert hs.score == 90  # 100 - 10
    assert hs.breakdown.audit_violations == 1


# ---------------------------------------------------------------------------
# combined
# ---------------------------------------------------------------------------

def test_combined_penalties_floor_at_zero():
    diff = _make_diff(missing=[f"K{i}" for i in range(8)], mismatched=[("X", ("a", "b"))])
    lint = _make_lint(*(["E001"] * 5))
    audit = _make_audit(*(["v"] * 4))
    hs = score_env(diff=diff, lint=lint, audit=audit)
    assert hs.score == 0
    assert hs.grade == "F"


# ---------------------------------------------------------------------------
# grade boundaries
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score,expected_grade", [
    (100, "A"), (90, "A"), (89, "B"), (75, "B"),
    (74, "C"), (60, "C"), (59, "D"), (40, "D"),
    (39, "F"), (0, "F"),
])
def test_grade_boundaries(score, expected_grade):
    from envdiff.scorer import _grade
    assert _grade(score) == expected_grade


def test_str_representation():
    hs = score_env()
    assert "100" in str(hs)
    assert "A" in str(hs)
