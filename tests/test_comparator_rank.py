"""Tests for envdiff.comparator_rank."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from envdiff.comparator_rank import RankEntry, RankResult, rank_envs


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> str:
    p = directory / name
    p.write_text(content)
    return str(p)


# ---------------------------------------------------------------------------
# RankEntry
# ---------------------------------------------------------------------------

def test_rank_entry_total_issues() -> None:
    e = RankEntry(name="a.env", missing_count=2, extra_count=1, mismatch_count=3)
    assert e.total_issues == 6


def test_rank_entry_zero_issues() -> None:
    e = RankEntry(name="clean.env", missing_count=0, extra_count=0, mismatch_count=0)
    assert e.total_issues == 0


# ---------------------------------------------------------------------------
# RankResult
# ---------------------------------------------------------------------------

def _make_result(*totals: tuple[str, int, int, int]) -> RankResult:
    entries = [
        RankEntry(name=n, missing_count=m, extra_count=x, mismatch_count=mm)
        for n, m, x, mm in totals
    ]
    entries.sort(key=lambda e: e.total_issues, reverse=True)
    return RankResult(entries=entries)


def test_rank_result_best_and_worst() -> None:
    result = _make_result(("a", 5, 0, 0), ("b", 1, 0, 0), ("c", 0, 0, 0))
    assert result.worst is not None and result.worst.name == "a"
    assert result.best is not None and result.best.name == "c"


def test_rank_result_empty_best_worst() -> None:
    result = RankResult(entries=[])
    assert result.best is None
    assert result.worst is None


def test_rank_result_summary_empty() -> None:
    result = RankResult(entries=[])
    assert result.summary() == "No targets to rank."


def test_rank_result_summary_lists_entries() -> None:
    result = _make_result(("a.env", 2, 1, 0), ("b.env", 0, 0, 0))
    text = result.summary()
    assert "2 target(s)" in text
    assert "a.env" in text
    assert "b.env" in text


# ---------------------------------------------------------------------------
# rank_envs integration
# ---------------------------------------------------------------------------

def test_rank_envs_orders_worst_first(env_dir: Path) -> None:
    base = _write(env_dir, ".env.base", "A=1\nB=2\nC=3\n")
    # target1 is missing B and C (2 issues)
    t1 = _write(env_dir, ".env.t1", "A=1\n")
    # target2 is missing only C (1 issue)
    t2 = _write(env_dir, ".env.t2", "A=1\nB=2\n")

    result = rank_envs(base, [t1, t2])
    assert result.entries[0].name == str(t1)
    assert result.entries[1].name == str(t2)


def test_rank_envs_clean_target_has_zero_issues(env_dir: Path) -> None:
    base = _write(env_dir, ".env.base", "A=1\nB=2\n")
    target = _write(env_dir, ".env.t", "A=1\nB=2\n")

    result = rank_envs(base, [target])
    assert result.entries[0].total_issues == 0


def test_rank_envs_mismatch_counted(env_dir: Path) -> None:
    base = _write(env_dir, ".env.base", "A=1\n")
    target = _write(env_dir, ".env.t", "A=99\n")

    result = rank_envs(base, [target])
    assert result.entries[0].mismatch_count == 1


def test_rank_envs_ignore_values_skips_mismatch(env_dir: Path) -> None:
    base = _write(env_dir, ".env.base", "A=1\n")
    target = _write(env_dir, ".env.t", "A=99\n")

    result = rank_envs(base, [target], ignore_values=True)
    assert result.entries[0].mismatch_count == 0
    assert result.entries[0].total_issues == 0
