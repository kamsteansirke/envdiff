"""Integration tests for the 'envdiff graph' CLI sub-command."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def _run(tmp_path: Path, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "envdiff", "graph", *extra_args],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )


def test_graph_subcommand_exits_zero(tmp_path):
    f = _write(tmp_path, ".env", "KEY=value\n")
    result = _run(tmp_path, str(f))
    assert result.returncode == 0


def test_graph_subcommand_output_contains_summary(tmp_path):
    f = _write(tmp_path, ".env", "A=1\nB=${A}\n")
    result = _run(tmp_path, str(f))
    assert "Graph summary" in result.stdout


def test_graph_subcommand_cycle_flag(tmp_path):
    f = _write(tmp_path, ".env", "X=${Y}\nY=${X}\n")
    result = _run(tmp_path, str(f), "--check-cycles")
    assert result.returncode == 1
    assert "cycle" in result.stderr.lower()


def test_graph_subcommand_undefined_flag(tmp_path):
    f = _write(tmp_path, ".env", "URL=http://${GHOST_HOST}/\n")
    result = _run(tmp_path, str(f), "--show-undefined")
    assert result.returncode == 0
    assert "GHOST_HOST" in result.stdout
