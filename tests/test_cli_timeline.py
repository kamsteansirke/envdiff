"""Tests for envdiff.cli_timeline."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

from envdiff.cli_timeline import add_timeline_subparser, _run_timeline


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _save_snap(path: Path, data: dict[str, str]) -> None:
    """Write a minimal snapshot JSON understood by EnvSnapshot.load."""
    payload = {
        "keys": [
            {"key": k, "value": v, "value_hash": None}
            for k, v in data.items()
        ]
    }
    path.write_text(json.dumps(payload))


class FakeArgs:
    def __init__(
        self,
        snapshots: list[str],
        labels: list[str] | None = None,
        show_values: bool = False,
    ) -> None:
        self.snapshots = snapshots
        self.labels = labels
        self.show_values = show_values


def test_add_timeline_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_timeline_subparser(sub)
    args = parser.parse_args(["timeline", "a.json", "b.json"])
    assert hasattr(args, "func")


def test_run_timeline_requires_two_snapshots(env_dir: Path, capsys):
    s1 = env_dir / "s1.json"
    _save_snap(s1, {"A": "1"})
    args = FakeArgs(snapshots=[str(s1)])
    rc = _run_timeline(args)  # type: ignore[arg-type]
    assert rc == 2


def test_run_timeline_label_count_mismatch(env_dir: Path, capsys):
    s1 = env_dir / "s1.json"
    s2 = env_dir / "s2.json"
    _save_snap(s1, {"A": "1"})
    _save_snap(s2, {"A": "2"})
    args = FakeArgs(snapshots=[str(s1), str(s2)], labels=["only-one"])
    rc = _run_timeline(args)  # type: ignore[arg-type]
    assert rc == 2


def test_run_timeline_no_changes_exits_zero(env_dir: Path, capsys):
    s1 = env_dir / "s1.json"
    s2 = env_dir / "s2.json"
    _save_snap(s1, {"A": "1"})
    _save_snap(s2, {"A": "1"})
    args = FakeArgs(snapshots=[str(s1), str(s2)])
    rc = _run_timeline(args)  # type: ignore[arg-type]
    assert rc == 0
    out = capsys.readouterr().out
    assert "No changes" in out


def test_run_timeline_with_changes_exits_one(env_dir: Path, capsys):
    s1 = env_dir / "s1.json"
    s2 = env_dir / "s2.json"
    _save_snap(s1, {"A": "old"})
    _save_snap(s2, {"A": "new"})
    args = FakeArgs(snapshots=[str(s1), str(s2)])
    rc = _run_timeline(args)  # type: ignore[arg-type]
    assert rc == 1
    out = capsys.readouterr().out
    assert "A" in out


def test_run_timeline_show_values(env_dir: Path, capsys):
    s1 = env_dir / "s1.json"
    s2 = env_dir / "s2.json"
    _save_snap(s1, {"DB": "postgres"})
    _save_snap(s2, {"DB": "mysql"})
    args = FakeArgs(snapshots=[str(s1), str(s2)], show_values=True)
    _run_timeline(args)  # type: ignore[arg-type]
    out = capsys.readouterr().out
    assert "postgres" in out
    assert "mysql" in out
