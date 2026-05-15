"""Score a matrix of env comparisons and produce an aggregate health report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from envdiff.comparator_matrix import MatrixResult
from envdiff.scorer import HealthScore, ScoreBreakdown, score_env


@dataclass
class MatrixScoreEntry:
    """Health score for a single (base, target) pair."""

    base: str
    target: str
    score: HealthScore

    def __str__(self) -> str:
        return f"{self.base} -> {self.target}: {self.score}"


@dataclass
class MatrixScoreReport:
    """Aggregate scoring across all pairs in a comparison matrix."""

    entries: List[MatrixScoreEntry] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def average_score(self) -> float:
        """Return the mean numeric score across all pairs (0–100)."""
        if not self.entries:
            return 100.0
        return sum(e.score.numeric for e in self.entries) / len(self.entries)

    def lowest_entry(self) -> MatrixScoreEntry | None:
        """Return the pair with the lowest health score."""
        if not self.entries:
            return None
        return min(self.entries, key=lambda e: e.score.numeric)

    def overall_grade(self) -> str:
        """Letter grade derived from the average numeric score."""
        avg = self.average_score()
        if avg >= 95:
            return "A"
        if avg >= 80:
            return "B"
        if avg >= 65:
            return "C"
        if avg >= 50:
            return "D"
        return "F"

    def summary(self) -> str:
        lines = [
            f"Matrix score: {self.average_score():.1f}/100 (grade {self.overall_grade()})",
            f"Pairs evaluated: {len(self.entries)}",
        ]
        worst = self.lowest_entry()
        if worst is not None:
            lines.append(f"Worst pair: {worst.base} -> {worst.target} ({worst.score})")  
        return "\n".join(lines)


def score_matrix(matrix: MatrixResult) -> MatrixScoreReport:
    """Produce a :class:`MatrixScoreReport` from a :class:`MatrixResult`."""
    entries: List[MatrixScoreEntry] = []
    for cell in matrix.cells:
        diff = cell.diff
        breakdown = ScoreBreakdown(
            missing_keys=len(diff.missing_in_target) + len(diff.missing_in_base),
            mismatched_keys=len(diff.mismatches),
        )
        hs = HealthScore(breakdown=breakdown)
        entries.append(MatrixScoreEntry(base=cell.base, target=cell.target, score=hs))
    entries.sort(key=lambda e: (e.base, e.target))
    return MatrixScoreReport(entries=entries)
