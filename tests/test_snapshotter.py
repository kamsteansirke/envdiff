"""Tests for envdiff.snapshotter."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envdiff.snapshotter import (
    EnvSnapshot,
    SnapshotEntry,
    capture_snapshot,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_capture_snapshot_keys(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "FOO=bar\nBAZ=qux\n")
    snap = capture_snapshot(f)
    assert set(snap.keys()) == {"FOO", "BAZ"}


def test_capture_snapshot_values(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "KEY=hello\n")
    snap = capture_snapshot(f)
    assert snap.entries["KEY"].value == "hello"


def test_capture_snapshot_ignore_values(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "SECRET=topsecret\n")
    snap = capture_snapshot(f, ignore_values=True)
    assert snap.entries["SECRET"].value == ""


def test_capture_snapshot_source(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "A=1\n")
    snap = capture_snapshot(f)
    assert snap.source == str(f)


def test_save_and_load_roundtrip(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "X=1\nY=2\n")
    snap = capture_snapshot(f)
    out = env_dir / "snap.json"
    save_snapshot(snap, out)
    loaded = load_snapshot(out)
    assert loaded.keys() == snap.keys()
    assert loaded.entries["X"].value == "1"
    assert loaded.source == snap.source


def test_load_snapshot_missing_file_raises(env_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_snapshot(env_dir / "nonexistent.json")


def test_diff_snapshots_no_change(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "A=1\n")
    snap = capture_snapshot(f)
    assert diff_snapshots(snap, snap) == {}


def test_diff_snapshots_added_key(env_dir: Path) -> None:
    old_f = _write(env_dir / "old.env", "A=1\n")
    new_f = _write(env_dir / "new.env", "A=1\nB=2\n")
    old = capture_snapshot(old_f)
    new = capture_snapshot(new_f)
    changes = diff_snapshots(old, new)
    assert changes["B"] == "added"


def test_diff_snapshots_removed_key(env_dir: Path) -> None:
    old_f = _write(env_dir / "old.env", "A=1\nB=2\n")
    new_f = _write(env_dir / "new.env", "A=1\n")
    old = capture_snapshot(old_f)
    new = capture_snapshot(new_f)
    changes = diff_snapshots(old, new)
    assert changes["B"] == "removed"


def test_diff_snapshots_changed_value(env_dir: Path) -> None:
    old_f = _write(env_dir / "old.env", "A=old\n")
    new_f = _write(env_dir / "new.env", "A=new\n")
    old = capture_snapshot(old_f)
    new = capture_snapshot(new_f)
    changes = diff_snapshots(old, new)
    assert changes["A"] == "changed"


def test_snapshot_entry_roundtrip() -> None:
    entry = SnapshotEntry(key="K", value="v", captured_at=time.time())
    restored = SnapshotEntry.from_dict(entry.to_dict())
    assert restored.key == entry.key
    assert restored.value == entry.value
