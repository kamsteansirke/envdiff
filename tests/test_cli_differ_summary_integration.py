"""Integration tests for the diff-summary sub-command via subprocess."""
from __future__ import annotations

import pathlib
import subprocess
import sys
import pytest

from envdiff.snapshotter import EnvSnapshot, SnapshotEntry


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _save_snap(path: pathlib.Path, pairs: dict) -> None:
    entries = {k: SnapshotEntry(key=k, value_hash=v) for k, v in pairs.items()}
    EnvSnapshot(entries=entries).save(str(path))


def _run(*args: str) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
    return subprocess.run(
        [sys.executable, "-m", "envdiff", *args],
        capture_output=True,
        text=True,
    )


def test_diff_summary_exits_zero_no_changes(env_dir):
    p1 = env_dir / "a.json"
    p2 = env_dir / "b.json"
    _save_snap(p1, {"FOO": "h1"})
    _save_snap(p2, {"FOO": "h1"})
    result = _run("diff-summary", str(p1), str(p2))
    assert result.returncode == 0


def test_diff_summary_exits_one_with_changes(env_dir):
    p1 = env_dir / "a.json"
    p2 = env_dir / "b.json"
    _save_snap(p1, {"FOO": "old"})
    _save_snap(p2, {"FOO": "new"})
    result = _run("diff-summary", str(p1), str(p2))
    assert result.returncode == 1


def test_diff_summary_output_contains_summary(env_dir):
    p1 = env_dir / "a.json"
    p2 = env_dir / "b.json"
    _save_snap(p1, {})
    _save_snap(p2, {"ADDED_KEY": "hash"})
    result = _run("diff-summary", str(p1), str(p2))
    assert "Summary:" in result.stdout
    assert "1 added" in result.stdout
