"""Summarizer: produce a human-readable health summary across multiple .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file
from envdiff.linter import lint_env, LintResult
from envdiff.profiler import profile_env, ProfileResult
from envdiff.scorer import score_env, HealthScore


@dataclass
class FileSummary:
    path: Path
    key_count: int
    empty_count: int
    lint_issues: int
    health_score: float
    grade: str

    def one_line(self) -> str:
        return (
            f"{self.path.name}: {self.key_count} keys, "
            f"{self.empty_count} empty, "
            f"{self.lint_issues} lint issue(s), "
            f"score={self.health_score:.1f} ({self.grade})"
        )


@dataclass
class SummaryReport:
    files: List[FileSummary] = field(default_factory=list)

    def overall_grade(self) -> str:
        if not self.files:
            return "N/A"
        avg = sum(f.health_score for f in self.files) / len(self.files)
        if avg >= 90:
            return "A"
        if avg >= 75:
            return "B"
        if avg >= 60:
            return "C"
        if avg >= 40:
            return "D"
        return "F"

    def render(self) -> str:
        if not self.files:
            return "No files summarized."
        lines = ["=== envdiff summary ==="]
        for fs in self.files:
            lines.append("  " + fs.one_line())
        lines.append(f"Overall grade: {self.overall_grade()}")
        return "\n".join(lines)


def summarize_files(paths: List[Path], ignore_values: bool = True) -> SummaryReport:
    """Summarize a list of .env file paths into a SummaryReport."""
    report = SummaryReport()
    for path in paths:
        env = parse_env_file(path)
        profile: ProfileResult = profile_env(env)
        lint: LintResult = lint_env(env)
        hs: HealthScore = score_env(diff=None, lint=lint, audit=None)
        fs = FileSummary(
            path=path,
            key_count=profile.total_keys,
            empty_count=profile.empty_count,
            lint_issues=len(lint.issues),
            health_score=hs.score,
            grade=hs.grade,
        )
        report.files.append(fs)
    return report
