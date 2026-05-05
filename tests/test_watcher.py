"""Tests for envdiff.watcher."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envdiff.watcher import EnvWatcher
from envdiff.comparator import EnvDiff


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def test_watcher_detects_no_change_initially(env_dir: Path) -> None:
    base = env_dir / ".env.base"
    target = env_dir / ".env.prod"
    _write(base, "KEY=value\n")
    _write(target, "KEY=value\n")

    calls: list[str] = []
    watcher = EnvWatcher(base, [target], on_change=lambda label, diff: calls.append(label))
    watcher._mtimes = watcher._snapshot()
    # no file changed — callback should not fire
    watcher._run_once()  # diffs are equal, so no call
    assert calls == []


def test_watcher_fires_callback_on_diff(env_dir: Path) -> None:
    base = env_dir / ".env.base"
    target = env_dir / ".env.prod"
    _write(base, "KEY=value\nEXTRA=base_only\n")
    _write(target, "KEY=value\n")

    received: list[tuple[str, EnvDiff]] = []
    watcher = EnvWatcher(base, [target], on_change=lambda l, d: received.append((l, d)))
    watcher._run_once()

    assert len(received) == 1
    label, diff = received[0]
    assert str(target) in label
    assert diff.has_differences()


def test_watcher_changed_paths_detects_modification(env_dir: Path) -> None:
    base = env_dir / ".env.base"
    target = env_dir / ".env.prod"
    _write(base, "A=1\n")
    _write(target, "A=1\n")

    watcher = EnvWatcher(base, [target])
    old = watcher._snapshot()
    watcher._mtimes = old

    # simulate mtime bump
    time.sleep(0.05)
    _write(target, "A=2\n")
    new = watcher._snapshot()
    changed = watcher._changed_paths(new)
    assert target in changed


def test_watcher_max_iterations(env_dir: Path) -> None:
    base = env_dir / ".env.base"
    target = env_dir / ".env.prod"
    _write(base, "A=1\n")
    _write(target, "A=1\n")

    watcher = EnvWatcher(base, [target], poll_interval=0.01)

    with patch.object(watcher, "_run_once") as mock_run:
        watcher.watch(max_iterations=3)
        assert mock_run.call_count == 3


def test_watcher_missing_file_returns_zero_mtime(env_dir: Path) -> None:
    base = env_dir / ".env.base"
    target = env_dir / ".env.missing"
    _write(base, "A=1\n")

    watcher = EnvWatcher(base, [target])
    assert watcher._mtime(target) == 0.0
