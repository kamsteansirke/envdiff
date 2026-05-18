"""Tests for envdiff.comparator_overlap."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.comparator_overlap import OverlapEntry, OverlapResult, analyze_overlap


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


# --- OverlapEntry ---

def test_entry_str_shows_key_and_sources():
    e = OverlapEntry(key="DB_HOST", present_in=frozenset({"prod", "dev"}))
    assert "DB_HOST" in str(e)
    assert "dev" in str(e)
    assert "prod" in str(e)


def test_entry_coverage_full():
    e = OverlapEntry(key="X", present_in=frozenset({"a", "b", "c"}))
    assert e.coverage(3) == pytest.approx(1.0)


def test_entry_coverage_partial():
    e = OverlapEntry(key="X", present_in=frozenset({"a"}))
    assert e.coverage(4) == pytest.approx(0.25)


def test_entry_coverage_zero_total():
    e = OverlapEntry(key="X", present_in=frozenset())
    assert e.coverage(0) == pytest.approx(0.0)


# --- analyze_overlap ---

def test_all_keys_present(env_dir: Path):
    a = _write(env_dir, "dev.env", "A=1\nB=2\n")
    b = _write(env_dir, "prod.env", "A=1\nC=3\n")
    result = analyze_overlap(a, b)
    assert set(result.all_keys()) == {"A", "B", "C"}


def test_universal_keys(env_dir: Path):
    a = _write(env_dir, "dev.env", "A=1\nB=2\n")
    b = _write(env_dir, "prod.env", "A=1\nC=3\n")
    result = analyze_overlap(a, b)
    assert result.universal_keys() == ["A"]


def test_unique_keys(env_dir: Path):
    a = _write(env_dir, "dev.env", "A=1\nB=2\n")
    b = _write(env_dir, "prod.env", "A=1\nC=3\n")
    result = analyze_overlap(a, b)
    assert set(result.unique_keys()) == {"B", "C"}


def test_fully_overlapping_true(env_dir: Path):
    a = _write(env_dir, "dev.env", "X=1\n")
    b = _write(env_dir, "prod.env", "X=2\n")
    result = analyze_overlap(a, b)
    assert result.is_fully_overlapping() is True


def test_fully_overlapping_false(env_dir: Path):
    a = _write(env_dir, "dev.env", "X=1\nY=2\n")
    b = _write(env_dir, "prod.env", "X=1\n")
    result = analyze_overlap(a, b)
    assert result.is_fully_overlapping() is False


def test_entry_for_known_key(env_dir: Path):
    a = _write(env_dir, "dev.env", "PORT=8080\n")
    b = _write(env_dir, "prod.env", "PORT=443\n")
    result = analyze_overlap(a, b)
    entry = result.entry_for("PORT")
    assert entry is not None
    assert "dev" in entry.present_in
    assert "prod" in entry.present_in


def test_entry_for_unknown_key_returns_none(env_dir: Path):
    a = _write(env_dir, "dev.env", "A=1\n")
    result = analyze_overlap(a)
    assert result.entry_for("MISSING") is None


def test_summary_contains_counts(env_dir: Path):
    a = _write(env_dir, "dev.env", "A=1\nB=2\n")
    b = _write(env_dir, "prod.env", "A=1\nC=3\n")
    result = analyze_overlap(a, b)
    summary = result.summary()
    assert "3 keys" in summary
    assert "2 files" in summary


def test_env_names_sorted(env_dir: Path):
    a = _write(env_dir, "zzz.env", "A=1\n")
    b = _write(env_dir, "aaa.env", "A=1\n")
    result = analyze_overlap(a, b)
    assert result.env_names == ["aaa", "zzz"]
