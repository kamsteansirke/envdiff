"""Tests for envdiff.cli_patch."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.cli_patch import add_patch_subparser, _run_patch


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def _make_args(env_file: Path, assignments=(), remove=(), no_add=False, dry_run=False):
    ns = argparse.Namespace(
        env_file=env_file,
        assignments=list(assignments),
        remove=list(remove),
        no_add=no_add,
        dry_run=dry_run,
    )
    return ns


def test_add_patch_subparser_registers_command() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_patch_subparser(sub)
    args = parser.parse_args(["patch", "/tmp/.env"])
    assert hasattr(args, "func")


def test_run_patch_applies_update(env_dir: Path) -> None:
    f = _write(env_dir, ".env", "FOO=old\n")
    args = _make_args(f, assignments=["FOO=new"])
    rc = _run_patch(args)
    assert rc == 0
    assert "FOO=new" in f.read_text()


def test_run_patch_invalid_assignment_returns_2(env_dir: Path, capsys) -> None:
    f = _write(env_dir, ".env", "FOO=bar\n")
    args = _make_args(f, assignments=["INVALID"])
    rc = _run_patch(args)
    assert rc == 2


def test_run_patch_dry_run_prints_prefix(env_dir: Path, capsys) -> None:
    f = _write(env_dir, ".env", "FOO=old\n")
    args = _make_args(f, assignments=["FOO=new"], dry_run=True)
    rc = _run_patch(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "dry-run" in out
    # File must NOT be modified
    assert "FOO=old" in f.read_text()


def test_run_patch_nothing_to_do_returns_0(env_dir: Path, capsys) -> None:
    f = _write(env_dir, ".env", "FOO=bar\n")
    args = _make_args(f)
    rc = _run_patch(args)
    assert rc == 0


def test_run_patch_remove_key(env_dir: Path) -> None:
    f = _write(env_dir, ".env", "FOO=bar\nBAZ=qux\n")
    args = _make_args(f, remove=["BAZ"])
    rc = _run_patch(args)
    assert rc == 0
    assert "BAZ" not in f.read_text()
