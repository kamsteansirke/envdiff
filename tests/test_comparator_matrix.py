"""Tests for envdiff.comparator_matrix."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.comparator_matrix import build_matrix, MatrixCell, MatrixResult


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> str:
    p = directory / name
    p.write_text(content)
    return str(p)


def test_build_matrix_returns_all_ordered_pairs(env_dir):
    a = _write(env_dir, "a.env", "KEY=1\nFOO=bar\n")
    b = _write(env_dir, "b.env", "KEY=1\nFOO=bar\n")
    result = build_matrix({"a": a, "b": b})
    assert result.cell("a", "b") is not None
    assert result.cell("b", "a") is not None
    assert result.cell("a", "a") is None


def test_clean_pair_is_clean(env_dir):
    a = _write(env_dir, "a.env", "KEY=1\n")
    b = _write(env_dir, "b.env", "KEY=1\n")
    result = build_matrix({"a": a, "b": b})
    assert result.cell("a", "b").is_clean
    assert not result.dirty_pairs()


def test_mismatched_values_marks_dirty(env_dir):
    a = _write(env_dir, "a.env", "KEY=1\n")
    b = _write(env_dir, "b.env", "KEY=2\n")
    result = build_matrix({"a": a, "b": b})
    assert not result.cell("a", "b").is_clean
    assert ("a", "b") in result.dirty_pairs()


def test_ignore_values_suppresses_value_mismatch(env_dir):
    a = _write(env_dir, "a.env", "KEY=1\n")
    b = _write(env_dir, "b.env", "KEY=2\n")
    result = build_matrix({"a": a, "b": b}, ignore_values=True)
    assert result.cell("a", "b").is_clean


def test_missing_key_marks_dirty(env_dir):
    a = _write(env_dir, "a.env", "KEY=1\nEXTRA=x\n")
    b = _write(env_dir, "b.env", "KEY=1\n")
    result = build_matrix({"a": a, "b": b})
    assert not result.cell("a", "b").is_clean


def test_env_names_sorted(env_dir):
    z = _write(env_dir, "z.env", "K=1\n")
    a = _write(env_dir, "a.env", "K=1\n")
    m = _write(env_dir, "m.env", "K=1\n")
    result = build_matrix({"z": z, "a": a, "m": m})
    assert result.env_names == ["a", "m", "z"]


def test_summary_string(env_dir):
    a = _write(env_dir, "a.env", "KEY=1\n")
    b = _write(env_dir, "b.env", "KEY=2\n")
    result = build_matrix({"a": a, "b": b})
    s = result.summary()
    assert "2 envs" in s
    assert "2 pairs" in s


def test_three_envs_pair_count(env_dir):
    a = _write(env_dir, "a.env", "K=1\n")
    b = _write(env_dir, "b.env", "K=1\n")
    c = _write(env_dir, "c.env", "K=1\n")
    result = build_matrix({"a": a, "b": b, "c": c})
    # 3 envs → 3*2 = 6 ordered pairs
    assert len(result._cells) == 6
