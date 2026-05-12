"""Tests for envdiff.cli_differ_summary."""
from __future__ import annotations

import json
import pathlib
import pytest

from envdiff.cli_differ_summary import add_differ_summary_subparser, _run_differ_summary
from envdiff.snapshotter import EnvSnapshot, SnapshotEntry


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _save_snap(path: pathlib.Path, pairs: dict) -> None:
    entries = {k: SnapshotEntry(key=k, value_hash=v) for k, v in pairs.items()}
    snap = EnvSnapshot(entries=entries)
    snap.save(str(path))


class FakeArgs:
    def __init__(self, before: str, after: str, show_values: bool = False):
        self.before = before
        self.after = after
        self.show_values = show_values


def test_add_differ_summary_subparser_registers_command():
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_differ_summary_subparser(sub)
    args = parser.parse_args(["diff-summary", "a.json", "b.json"])
    assert args.before == "a.json"
    assert args.after == "b.json"


def test_run_diff_summary_no_changes_returns_zero(env_dir):
    p1 = env_dir / "snap1.json"
    p2 = env_dir / "snap2.json"
    _save_snap(p1, {"KEY": "hash"})
    _save_snap(p2, {"KEY": "hash"})
    args = FakeArgs(str(p1), str(p2))
    assert _run_differ_summary(args) == 0


def test_run_diff_summary_with_changes_returns_one(env_dir):
    p1 = env_dir / "snap1.json"
    p2 = env_dir / "snap2.json"
    _save_snap(p1, {"KEY": "hash_old"})
    _save_snap(p2, {"KEY": "hash_new"})
    args = FakeArgs(str(p1), str(p2))
    assert _run_differ_summary(args) == 1


def test_run_diff_summary_missing_file_returns_two(env_dir):
    p1 = env_dir / "snap1.json"
    _save_snap(p1, {})
    args = FakeArgs(str(p1), str(env_dir / "missing.json"))
    assert _run_differ_summary(args) == 2


def test_run_diff_summary_show_values_flag(env_dir, capsys):
    p1 = env_dir / "snap1.json"
    p2 = env_dir / "snap2.json"
    _save_snap(p1, {"K": "old"})
    _save_snap(p2, {"K": "new"})
    args = FakeArgs(str(p1), str(p2), show_values=True)
    _run_differ_summary(args)
    captured = capsys.readouterr()
    assert "->" in captured.out
