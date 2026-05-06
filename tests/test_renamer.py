"""Tests for envdiff.renamer and envdiff.cli_rename."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pytest

from envdiff.renamer import RenameCandidate, RenameResult, detect_renames
from envdiff.cli_rename import add_rename_subparser, _run_rename


# ---------------------------------------------------------------------------
# detect_renames unit tests
# ---------------------------------------------------------------------------

def test_no_changes_returns_empty():
    env = {"A": "1", "B": "2"}
    result = detect_renames(env, env)
    assert not result.has_candidates
    assert result.unmatched_removed == []
    assert result.unmatched_added == []


def test_exact_rename_detected():
    base = {"OLD_KEY": "hello"}
    target = {"NEW_KEY": "hello"}
    result = detect_renames(base, target)
    assert len(result.candidates) == 1
    c = result.candidates[0]
    assert c.old_key == "OLD_KEY"
    assert c.new_key == "NEW_KEY"
    assert c.value == "hello"
    assert c.confidence == "exact"
    assert result.unmatched_removed == []
    assert result.unmatched_added == []


def test_only_removed_no_candidate():
    base = {"GONE": "val"}
    target = {}
    result = detect_renames(base, target)
    assert not result.has_candidates
    assert "GONE" in result.unmatched_removed


def test_only_added_no_candidate():
    base = {}
    target = {"NEW": "val"}
    result = detect_renames(base, target)
    assert not result.has_candidates
    assert "NEW" in result.unmatched_added


def test_value_mismatch_not_a_candidate():
    base = {"OLD": "foo"}
    target = {"NEW": "bar"}
    result = detect_renames(base, target)
    assert not result.has_candidates
    assert "OLD" in result.unmatched_removed
    assert "NEW" in result.unmatched_added


def test_multiple_renames():
    base = {"A": "1", "B": "2"}
    target = {"X": "1", "Y": "2"}
    result = detect_renames(base, target)
    assert len(result.candidates) == 2
    pairs = {(c.old_key, c.new_key) for c in result.candidates}
    assert ("A", "X") in pairs
    assert ("B", "Y") in pairs


def test_partial_rename_with_leftovers():
    base = {"OLD": "same", "REMOVED": "gone"}
    target = {"NEW": "same", "ADDED": "fresh"}
    result = detect_renames(base, target)
    assert len(result.candidates) == 1
    assert result.candidates[0].old_key == "OLD"
    assert result.candidates[0].new_key == "NEW"
    assert "REMOVED" in result.unmatched_removed
    assert "ADDED" in result.unmatched_added


def test_summary_no_candidates():
    result = RenameResult()
    assert result.summary() == "No rename candidates found."


def test_str_rename_candidate():
    c = RenameCandidate("OLD", "NEW", "val", "exact")
    assert "OLD" in str(c)
    assert "NEW" in str(c)
    assert "exact" in str(c)


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def test_add_rename_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_rename_subparser(sub)
    args = parser.parse_args(["rename", "base.env", "target.env"])
    assert args.func is not None


def test_run_rename_no_candidates(env_dir: Path):
    base = _write(env_dir, "base.env", "KEY=value\n")
    target = _write(env_dir, "target.env", "KEY=value\n")
    ns = argparse.Namespace(base=str(base), target=str(target), no_color=True, func=_run_rename)
    assert _run_rename(ns) == 0


def test_run_rename_detects_rename(env_dir: Path):
    base = _write(env_dir, "base.env", "OLD_KEY=secret\n")
    target = _write(env_dir, "target.env", "NEW_KEY=secret\n")
    ns = argparse.Namespace(base=str(base), target=str(target), no_color=True, func=_run_rename)
    assert _run_rename(ns) == 1


def test_run_rename_missing_file_returns_2(env_dir: Path):
    ns = argparse.Namespace(
        base=str(env_dir / "nope.env"),
        target=str(env_dir / "also_nope.env"),
        no_color=True,
        func=_run_rename,
    )
    assert _run_rename(ns) == 2
