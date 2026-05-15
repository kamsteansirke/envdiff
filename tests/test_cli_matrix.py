"""Unit tests for envdiff.cli_matrix."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.cli_matrix import add_matrix_subparser, _run_matrix


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> str:
    p = directory / name
    p.write_text(content)
    return str(p)


class FakeArgs:
    def __init__(self, files, ignore_values=False, no_color=True):
        self.files = files
        self.ignore_values = ignore_values
        self.no_color = no_color


def test_add_matrix_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_matrix_subparser(sub)
    parsed = parser.parse_args(["matrix", "a.env", "b.env"])
    assert hasattr(parsed, "func")


def test_add_matrix_subparser_defaults():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_matrix_subparser(sub)
    parsed = parser.parse_args(["matrix", "a.env", "b.env"])
    assert parsed.ignore_values is False
    assert parsed.no_color is False


def test_run_matrix_exits_zero_when_clean(env_dir, capsys):
    a = _write(env_dir, "a.env", "KEY=1\n")
    b = _write(env_dir, "b.env", "KEY=1\n")
    code = _run_matrix(FakeArgs(files=[a, b]))
    assert code == 0


def test_run_matrix_exits_one_when_diff(env_dir, capsys):
    a = _write(env_dir, "a.env", "KEY=1\n")
    b = _write(env_dir, "b.env", "KEY=2\n")
    code = _run_matrix(FakeArgs(files=[a, b]))
    assert code == 1


def test_run_matrix_too_few_files(env_dir, capsys):
    a = _write(env_dir, "a.env", "KEY=1\n")
    code = _run_matrix(FakeArgs(files=[a]))
    assert code == 2


def test_run_matrix_output_contains_ok(env_dir, capsys):
    a = _write(env_dir, "a.env", "KEY=1\n")
    b = _write(env_dir, "b.env", "KEY=1\n")
    _run_matrix(FakeArgs(files=[a, b]))
    out = capsys.readouterr().out
    assert "OK" in out


def test_run_matrix_output_contains_diff(env_dir, capsys):
    a = _write(env_dir, "a.env", "KEY=1\n")
    b = _write(env_dir, "b.env", "KEY=2\n")
    _run_matrix(FakeArgs(files=[a, b]))
    out = capsys.readouterr().out
    assert "DIFF" in out
