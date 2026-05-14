"""Tests for envdiff.cli_stale."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.cli_stale import add_stale_subparser, _run_stale


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


class FakeArgs:
    def __init__(self, file: str, exit_zero: bool = False):
        self.file = file
        self.exit_zero = exit_zero


# ---------------------------------------------------------------------------
# Subparser registration
# ---------------------------------------------------------------------------

def test_add_stale_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_stale_subparser(sub)
    args = parser.parse_args(["stale", "some.env"])
    assert hasattr(args, "func")


def test_add_stale_subparser_defaults():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_stale_subparser(sub)
    args = parser.parse_args(["stale", "my.env"])
    assert args.exit_zero is False


# ---------------------------------------------------------------------------
# _run_stale
# ---------------------------------------------------------------------------

def test_run_stale_clean_file_exits_zero(env_dir):
    p = _write(env_dir, ".env", "DB_HOST=db.prod.internal\nPORT=5432\n")
    assert _run_stale(FakeArgs(str(p))) == 0


def test_run_stale_stale_value_exits_one(env_dir):
    p = _write(env_dir, ".env", "API_KEY=changeme\n")
    assert _run_stale(FakeArgs(str(p))) == 1


def test_run_stale_exit_zero_flag_overrides(env_dir):
    p = _write(env_dir, ".env", "API_KEY=changeme\n")
    assert _run_stale(FakeArgs(str(p), exit_zero=True)) == 0


def test_run_stale_missing_file_exits_two(env_dir):
    assert _run_stale(FakeArgs(str(env_dir / "missing.env"))) == 2


def test_run_stale_output_contains_key(env_dir, capsys):
    p = _write(env_dir, ".env", "SECRET=placeholder\n")
    _run_stale(FakeArgs(str(p)))
    out = capsys.readouterr().out
    assert "SECRET" in out
