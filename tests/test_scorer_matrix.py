"""Tests for envdiff.scorer_matrix."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.comparator_matrix import build_matrix
from envdiff.scorer_matrix import MatrixScoreEntry, MatrixScoreReport, score_matrix


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# MatrixScoreReport unit tests
# ---------------------------------------------------------------------------


def _make_report(*numerics: float) -> MatrixScoreReport:
    from envdiff.scorer import HealthScore, ScoreBreakdown

    entries = []
    for i, n in enumerate(numerics):
        # back-calculate missing_keys to approximate the desired numeric
        missing = max(0, round((100 - n) / 5))
        bd = ScoreBreakdown(missing_keys=missing, mismatched_keys=0)
        hs = HealthScore(breakdown=bd)
        entries.append(MatrixScoreEntry(base=f"base{i}", target=f"target{i}", score=hs))
    return MatrixScoreReport(entries=entries)


def test_empty_report_average_is_100() -> None:
    report = MatrixScoreReport()
    assert report.average_score() == 100.0


def test_empty_report_grade_is_A() -> None:
    report = MatrixScoreReport()
    assert report.overall_grade() == "A"


def test_empty_report_lowest_entry_is_none() -> None:
    report = MatrixScoreReport()
    assert report.lowest_entry() is None


def test_average_score_computed_correctly() -> None:
    report = _make_report(100.0, 100.0)
    assert report.average_score() == pytest.approx(100.0, abs=1.0)


def test_lowest_entry_returns_min() -> None:
    report = _make_report(100.0, 80.0, 60.0)
    worst = report.lowest_entry()
    assert worst is not None
    assert worst.score.numeric <= 65.0


def test_summary_contains_grade(env_dir: Path) -> None:
    report = MatrixScoreReport()
    s = report.summary()
    assert "grade" in s
    assert "A" in s


# ---------------------------------------------------------------------------
# score_matrix integration tests
# ---------------------------------------------------------------------------


def test_score_matrix_all_match(env_dir: Path) -> None:
    a = _write(env_dir, "a.env", "KEY=value\nFOO=bar\n")
    b = _write(env_dir, "b.env", "KEY=value\nFOO=bar\n")
    matrix = build_matrix([str(a), str(b)])
    report = score_matrix(matrix)
    assert report.average_score() == pytest.approx(100.0, abs=0.1)
    assert report.overall_grade() == "A"


def test_score_matrix_detects_missing_key(env_dir: Path) -> None:
    a = _write(env_dir, "a.env", "KEY=value\nEXTRA=only_in_a\n")
    b = _write(env_dir, "b.env", "KEY=value\n")
    matrix = build_matrix([str(a), str(b)])
    report = score_matrix(matrix)
    # At least one pair should be below perfect
    assert report.average_score() < 100.0


def test_score_matrix_entries_sorted(env_dir: Path) -> None:
    a = _write(env_dir, "a.env", "K=1\n")
    b = _write(env_dir, "b.env", "K=1\n")
    c = _write(env_dir, "c.env", "K=1\n")
    matrix = build_matrix([str(a), str(b), str(c)])
    report = score_matrix(matrix)
    bases = [e.base for e in report.entries]
    assert bases == sorted(bases)


def test_matrix_score_entry_str() -> None:
    from envdiff.scorer import HealthScore, ScoreBreakdown

    bd = ScoreBreakdown(missing_keys=0, mismatched_keys=0)
    hs = HealthScore(breakdown=bd)
    entry = MatrixScoreEntry(base="dev", target="prod", score=hs)
    assert "dev" in str(entry)
    assert "prod" in str(entry)
