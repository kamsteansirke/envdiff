"""Tests for envdiff.cli_watch."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envdiff.cli_watch import add_watch_subparser, _run_watch


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> None:
    path.write_text(content)


def _make_args(base: Path, targets: list[Path], **kwargs) -> argparse.Namespace:  # type: ignore[type-arg]
    defaults = {"interval": 2.0, "show_values": False, "no_color": True}
    defaults.update(kwargs)
    return argparse.Namespace(base=base, targets=targets, **defaults)


def test_add_watch_subparser_registers_command() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_watch_subparser(sub)
    args = parser.parse_args(["watch", ".env", ".env.prod"])
    assert args.base == Path(".env")
    assert args.targets == [Path(".env.prod")]


def test_add_watch_subparser_defaults() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_watch_subparser(sub)
    args = parser.parse_args(["watch", ".env", ".env.prod"])
    assert args.interval == 2.0
    assert args.show_values is False
    assert args.no_color is False


def test_run_watch_calls_watcher(env_dir: Path) -> None:
    base = env_dir / ".env"
    target = env_dir / ".env.prod"
    _write(base, "KEY=1\n")
    _write(target, "KEY=1\n")

    args = _make_args(base, [target])

    with patch("envdiff.cli_watch.EnvWatcher") as MockWatcher:
        instance = MagicMock()
        MockWatcher.return_value = instance
        _run_watch(args)
        MockWatcher.assert_called_once()
        instance.watch.assert_called_once()


def test_run_watch_passes_interval(env_dir: Path) -> None:
    base = env_dir / ".env"
    target = env_dir / ".env.prod"
    _write(base, "KEY=1\n")
    _write(target, "KEY=1\n")

    args = _make_args(base, [target], interval=5.0)

    with patch("envdiff.cli_watch.EnvWatcher") as MockWatcher:
        instance = MagicMock()
        MockWatcher.return_value = instance
        _run_watch(args)
        _, kwargs = MockWatcher.call_args
        assert kwargs["poll_interval"] == 5.0


def test_run_watch_returns_zero(env_dir: Path) -> None:
    base = env_dir / ".env"
    target = env_dir / ".env.prod"
    _write(base, "KEY=1\n")
    _write(target, "KEY=1\n")

    args = _make_args(base, [target])

    with patch("envdiff.cli_watch.EnvWatcher") as MockWatcher:
        MockWatcher.return_value = MagicMock()
        result = _run_watch(args)
    assert result == 0
