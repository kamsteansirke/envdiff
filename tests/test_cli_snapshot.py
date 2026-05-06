"""Tests for envdiff.cli_snapshot."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.cli_snapshot import _run_capture, _run_diff
from envdiff.snapshotter import capture_snapshot, save_snapshot


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


class FakeArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_run_capture_creates_snapshot(env_dir: Path) -> None:
    env = _write(env_dir / ".env", "FOO=bar\n")
    out = env_dir / "snap.json"
    args = FakeArgs(env_file=str(env), output=str(out), ignore_values=False)
    rc = _run_capture(args)
    assert rc == 0
    assert out.exists()
    data = json.loads(out.read_text())
    assert "FOO" in data["entries"]


def test_run_capture_missing_file_returns_1(env_dir: Path) -> None:
    args = FakeArgs(
        env_file=str(env_dir / "missing.env"),
        output=str(env_dir / "snap.json"),
        ignore_values=False,
    )
    rc = _run_capture(args)
    assert rc == 1


def test_run_capture_ignore_values(env_dir: Path) -> None:
    env = _write(env_dir / ".env", "SECRET=topsecret\n")
    out = env_dir / "snap.json"
    args = FakeArgs(env_file=str(env), output=str(out), ignore_values=True)
    _run_capture(args)
    data = json.loads(out.read_text())
    assert data["entries"]["SECRET"]["value"] == ""


def test_run_diff_no_changes(env_dir: Path, capsys) -> None:
    env = _write(env_dir / ".env", "A=1\n")
    snap = capture_snapshot(env)
    p1 = env_dir / "s1.json"
    p2 = env_dir / "s2.json"
    save_snapshot(snap, p1)
    save_snapshot(snap, p2)
    args = FakeArgs(old=str(p1), new=str(p2))
    rc = _run_diff(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No changes" in out


def test_run_diff_detects_added(env_dir: Path, capsys) -> None:
    old_env = _write(env_dir / "old.env", "A=1\n")
    new_env = _write(env_dir / "new.env", "A=1\nB=2\n")
    p1 = env_dir / "s1.json"
    p2 = env_dir / "s2.json"
    save_snapshot(capture_snapshot(old_env), p1)
    save_snapshot(capture_snapshot(new_env), p2)
    args = FakeArgs(old=str(p1), new=str(p2))
    rc = _run_diff(args)
    assert rc == 1
    out = capsys.readouterr().out
    assert "B" in out
    assert "added" in out


def test_run_diff_missing_file_returns_1(env_dir: Path) -> None:
    args = FakeArgs(
        old=str(env_dir / "no_old.json"),
        new=str(env_dir / "no_new.json"),
    )
    rc = _run_diff(args)
    assert rc == 1
