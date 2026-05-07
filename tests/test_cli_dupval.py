"""Tests for envdiff.cli_dupval."""
from __future__ import annotations

import argparse
import pytest

from envdiff.cli_dupval import add_dupval_subparser, _run_dupval


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(directory, name: str, content: str) -> str:
    p = directory / name
    p.write_text(content)
    return str(p)


class FakeArgs:
    def __init__(self, files, include_empty=False, quiet=False):
        self.files = files
        self.include_empty = include_empty
        self.quiet = quiet


def test_add_dupval_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_dupval_subparser(sub)
    args = parser.parse_args(["dupval", "some.env"])
    assert args.command == "dupval"


def test_add_dupval_subparser_defaults():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_dupval_subparser(sub)
    args = parser.parse_args(["dupval", "a.env"])
    assert args.include_empty is False
    assert args.quiet is False


def test_run_dupval_no_duplicates_exits_zero(env_dir):
    path = _write(env_dir, ".env", "A=1\nB=2\n")
    args = FakeArgs(files=[path])
    assert _run_dupval(args) == 0


def test_run_dupval_with_duplicates_exits_one(env_dir):
    path = _write(env_dir, ".env", "A=same\nB=same\n")
    args = FakeArgs(files=[path])
    assert _run_dupval(args) == 1


def test_run_dupval_quiet_suppresses_output(env_dir, capsys):
    path = _write(env_dir, ".env", "A=same\nB=same\n")
    args = FakeArgs(files=[path], quiet=True)
    _run_dupval(args)
    captured = capsys.readouterr()
    assert captured.out == ""


def test_run_dupval_include_empty_flag(env_dir):
    path = _write(env_dir, ".env", "A=\nB=\n")
    args_ignore = FakeArgs(files=[path], include_empty=False)
    args_include = FakeArgs(files=[path], include_empty=True)
    assert _run_dupval(args_ignore) == 0
    assert _run_dupval(args_include) == 1


def test_run_dupval_multiple_files(env_dir):
    p1 = _write(env_dir, "a.env", "X=1\nY=2\n")
    p2 = _write(env_dir, "b.env", "X=dup\nY=dup\n")
    args = FakeArgs(files=[p1, p2])
    assert _run_dupval(args) == 1
