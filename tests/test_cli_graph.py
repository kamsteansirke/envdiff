"""Tests for envdiff.cli_graph."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.cli_graph import _run_graph, add_graph_subparser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


class FakeArgs:
    def __init__(self, file: str, show_undefined: bool = False, check_cycles: bool = False):
        self.file = file
        self.show_undefined = show_undefined
        self.check_cycles = check_cycles


# ---------------------------------------------------------------------------
# add_graph_subparser
# ---------------------------------------------------------------------------

def test_add_graph_subparser_registers_command():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_graph_subparser(sub)
    args = root.parse_args(["graph", "some.env"])
    assert args.func is _run_graph


def test_add_graph_subparser_defaults():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_graph_subparser(sub)
    args = root.parse_args(["graph", "x.env"])
    assert args.show_undefined is False
    assert args.check_cycles is False


# ---------------------------------------------------------------------------
# _run_graph
# ---------------------------------------------------------------------------

def test_run_graph_exits_zero_no_refs(tmp_path, capsys):
    f = _write(tmp_path, ".env", "A=1\nB=2\n")
    rc = _run_graph(FakeArgs(str(f)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "2 keys" in out


def test_run_graph_shows_reference(tmp_path, capsys):
    f = _write(tmp_path, ".env", "HOST=localhost\nURL=http://${HOST}/\n")
    rc = _run_graph(FakeArgs(str(f)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "URL" in out
    assert "HOST" in out


def test_run_graph_show_undefined(tmp_path, capsys):
    f = _write(tmp_path, ".env", "URL=http://${MISSING}/\n")
    rc = _run_graph(FakeArgs(str(f), show_undefined=True))
    assert rc == 0
    out = capsys.readouterr().out
    assert "MISSING" in out


def test_run_graph_check_cycles_exits_one(tmp_path):
    f = _write(tmp_path, ".env", "A=${B}\nB=${A}\n")
    rc = _run_graph(FakeArgs(str(f), check_cycles=True))
    assert rc == 1


def test_run_graph_check_cycles_no_cycle_exits_zero(tmp_path):
    f = _write(tmp_path, ".env", "A=1\nB=${A}\n")
    rc = _run_graph(FakeArgs(str(f), check_cycles=True))
    assert rc == 0


def test_run_graph_missing_file_exits_two(tmp_path):
    rc = _run_graph(FakeArgs(str(tmp_path / "nonexistent.env")))
    assert rc == 2
