"""Tests for envdiff.cli_group."""
import argparse
from pathlib import Path

import pytest

from envdiff.cli_group import add_group_subparser, _run_group


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def _make_args(files, separator="_", min_group_size=2):
    ns = argparse.Namespace(
        files=[str(f) for f in files],
        separator=separator,
        min_group_size=min_group_size,
    )
    return ns


# ---------------------------------------------------------------------------
# Subparser registration
# ---------------------------------------------------------------------------

def test_add_group_subparser_registers_command():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_group_subparser(sub)
    args = root.parse_args(["group", "some.env"])
    assert args.func is _run_group


def test_add_group_subparser_defaults():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_group_subparser(sub)
    args = root.parse_args(["group", "some.env"])
    assert args.separator == "_"
    assert args.min_group_size == 2


# ---------------------------------------------------------------------------
# _run_group
# ---------------------------------------------------------------------------

def test_run_group_exit_zero(env_dir, capsys):
    f = _write(env_dir, ".env", "DB_HOST=localhost\nDB_PORT=5432\nDEBUG=true\n")
    code = _run_group(_make_args([f]))
    assert code == 0


def test_run_group_shows_group_name(env_dir, capsys):
    f = _write(env_dir, ".env", "DB_HOST=localhost\nDB_PORT=5432\n")
    _run_group(_make_args([f]))
    out = capsys.readouterr().out
    assert "[DB]" in out


def test_run_group_shows_ungrouped(env_dir, capsys):
    f = _write(env_dir, ".env", "DB_HOST=localhost\nDB_PORT=5432\nDEBUG=true\n")
    _run_group(_make_args([f]))
    out = capsys.readouterr().out
    assert "ungrouped" in out
    assert "DEBUG" in out


def test_run_group_missing_file_returns_1(env_dir, capsys):
    code = _run_group(_make_args([env_dir / "nonexistent.env"]))
    assert code == 1
    err = capsys.readouterr().err
    assert "not found" in err


def test_run_group_multiple_files(env_dir, capsys):
    f1 = _write(env_dir, ".env.dev", "DB_HOST=dev\nDB_PORT=5432\n")
    f2 = _write(env_dir, ".env.prod", "AWS_KEY=k\nAWS_SECRET=s\n")
    code = _run_group(_make_args([f1, f2]))
    assert code == 0
    out = capsys.readouterr().out
    assert ".env.dev" in out
    assert ".env.prod" in out
    assert "[DB]" in out
    assert "[AWS]" in out


def test_run_group_custom_min_group_size(env_dir, capsys):
    # With min_group_size=1, a single DB_HOST should form a group
    f = _write(env_dir, ".env", "DB_HOST=localhost\nDEBUG=true\n")
    _run_group(_make_args([f], min_group_size=1))
    out = capsys.readouterr().out
    assert "[DB]" in out
