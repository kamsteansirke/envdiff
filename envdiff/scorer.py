"""Score the overall health of a .env file set based on diff, lint, and audit results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envdiff.comparator import EnvDiff
from envdiff.linter import LintResult
from envdiff.auditor import AuditResult


_WEIGHT_MISSING = 10
_WEIGHT_EXTRA = 5
_WEIGHT_MISMATCH = 7
_WEIGHT_LINT_ERROR = 8
_WEIGHT_LINT_WARN = 3
_WEIGHT_AUDIT = 10


@dataclass
class ScoreBreakdown:
    missing_keys: int = 0
    extra_keys: int = 0
    mismatched_keys: int = 0
    lint_errors: int = 0
    lint_warnings: int = 0
    audit_violations: int = 0

    @property
    def penalty(self) -> int:
        return (
            self.missing_keys * _WEIGHT_MISSING
            + self.extra_keys * _WEIGHT_EXTRA
            + self.mismatched_keys * _WEIGHT_MISMATCH
            + self.lint_errors * _WEIGHT_LINT_ERROR
            + self.lint_warnings * _WEIGHT_LINT_WARN
            + self.audit_violations * _WEIGHT_AUDIT
        )


@dataclass
class HealthScore:
    score: int  # 0-100
    grade: str
    breakdown: ScoreBreakdown
    notes: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Score: {self.score}/100 (Grade: {self.grade})"


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def score_env(
    diff: Optional[EnvDiff] = None,
    lint: Optional[LintResult] = None,
    audit: Optional[AuditResult] = None,
) -> HealthScore:
    """Compute a 0-100 health score from any combination of results."""
    breakdown = ScoreBreakdown()
    notes: List[str] = []

    if diff is not None:
        breakdown.missing_keys = len(diff.missing_in_target)
        breakdown.extra_keys = len(diff.missing_in_base)
        breakdown.mismatched_keys = len(diff.mismatched)
        if breakdown.missing_keys:
            notes.append(f"{breakdown.missing_keys} key(s) missing in target")
        if breakdown.extra_keys:
            notes.append(f"{breakdown.extra_keys} extra key(s) in target")
        if breakdown.mismatched_keys:
            notes.append(f"{breakdown.mismatched_keys} mismatched value(s)")

    if lint is not None:
        errors = [i for i in lint.issues if i.code.startswith("E")]
        warnings = [i for i in lint.issues if i.code.startswith("W")]
        breakdown.lint_errors = len(errors)
        breakdown.lint_warnings = len(warnings)
        if errors:
            notes.append(f"{len(errors)} lint error(s)")
        if warnings:
            notes.append(f"{len(warnings)} lint warning(s)")

    if audit is not None:
        breakdown.audit_violations = len(audit.violations)
        if audit.violations:
            notes.append(f"{len(audit.violations)} audit violation(s)")

    raw_score = max(0, 100 - breakdown.penalty)
    return HealthScore(
        score=raw_score,
        grade=_grade(raw_score),
        breakdown=breakdown,
        notes=notes,
    )
