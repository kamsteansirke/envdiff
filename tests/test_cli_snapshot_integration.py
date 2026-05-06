"""Integration tests for the snapshot subcommand via CLI entry point."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "envdiff", *args],
        capture_output=True,
        text=True,
    )


def test_snapshot_capture_exits_zero(env_dir: Path) -> None:
    env = _write(env_dir / ".env", "FOO=bar\n")
    out = env_dir / "snap.json"
    result = _run("snapshot", "capture", str(env), str(out))
    assert result.returncode == 0
    assert out.exists()


def test_snapshot_capture_output_contains_key_count(env_dir: Path) -> None:
    env = _write(env_dir / ".env", "A=1\nB=2\n")
    out = env_dir / "snap.json"
    result = _run("snapshot", "capture", str(env), str(out))
    assert "2 keys" in result.stdout


def test_snapshot_diff_no_change_exits_zero(env_dir: Path) -> None:
    env = _write(env_dir / ".env", "X=1\n")
    s1 = env_dir / "s1.json"
    s2 = env_dir / "s2.json"
    _run("snapshot", "capture", str(env), str(s1))
    _run("snapshot", "capture", str(env), str(s2))
    result = _run("snapshot", "diff", str(s1), str(s2))
    assert result.returncode == 0


def test_snapshot_diff_with_change_exits_one(env_dir: Path) -> None:
    old = _write(env_dir / "old.env", "A=1\n")
    new = _write(env_dir / "new.env", "A=1\nB=2\n")
    s1 = env_dir / "s1.json"
    s2 = env_dir / "s2.json"
    _run("snapshot", "capture", str(old), str(s1))
    _run("snapshot", "capture", str(new), str(s2))
    result = _run("snapshot", "diff", str(s1), str(s2))
    assert result.returncode == 1
    assert "B" in result.stdout
