"""Tests for envdiff.cli_pivot."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.cli_pivot import add_pivot_subparser, _run_pivot


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


class FakeArgs:
    def __init__(self, files, show_values=False, only_gaps=False, only_mismatches=False, no_color=True):
        self.files = files
        self.show_values = show_values
        self.only_gaps = only_gaps
        self.only_mismatches = only_mismatches
        self.no_color = no_color


def test_add_pivot_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_pivot_subparser(sub)
    args = parser.parse_args(["pivot", "a.env", "b.env"])
    assert hasattr(args, "func")


def test_run_pivot_exits_zero_when_identical(env_dir):
    a = _write(env_dir, ".env.dev", "KEY=value\nOTHER=x\n")
    b = _write(env_dir, ".env.prod", "KEY=value\nOTHER=x\n")
    args = FakeArgs(files=[str(a), str(b)])
    assert _run_pivot(args) == 0


def test_run_pivot_exits_one_on_missing_key(env_dir):
    a = _write(env_dir, ".env.dev", "KEY=value\nEXTRA=1\n")
    b = _write(env_dir, ".env.prod", "KEY=value\n")
    args = FakeArgs(files=[str(a), str(b)])
    assert _run_pivot(args) == 1


def test_run_pivot_exits_one_on_mismatch(env_dir):
    a = _write(env_dir, ".env.dev", "KEY=dev_val\n")
    b = _write(env_dir, ".env.prod", "KEY=prod_val\n")
    args = FakeArgs(files=[str(a), str(b)])
    assert _run_pivot(args) == 1


def test_run_pivot_returns_two_on_bad_file(env_dir):
    args = FakeArgs(files=["/nonexistent/path/.env"])
    assert _run_pivot(args) == 2


def test_run_pivot_only_gaps_filters_rows(env_dir, capsys):
    a = _write(env_dir, ".env.dev", "A=1\nB=2\n")
    b = _write(env_dir, ".env.prod", "A=1\n")
    args = FakeArgs(files=[str(a), str(b)], only_gaps=True)
    _run_pivot(args)
    captured = capsys.readouterr()
    assert "B" in captured.out
    assert "A" not in captured.out.splitlines()[2]  # header + separator + first data row


def test_run_pivot_show_values_displays_value(env_dir, capsys):
    a = _write(env_dir, ".env.dev", "SECRET=hunter2\n")
    b = _write(env_dir, ".env.prod", "SECRET=hunter2\n")
    args = FakeArgs(files=[str(a), str(b)], show_values=True)
    _run_pivot(args)
    captured = capsys.readouterr()
    assert "hunter2" in captured.out
