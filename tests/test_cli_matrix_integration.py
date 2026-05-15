"""Integration tests for the 'matrix' CLI sub-command."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "envdiff", *args],
        capture_output=True,
        text=True,
    )


def test_matrix_subcommand_exits_zero_all_match(env_dir):
    a = _write(env_dir, "a.env", "KEY=hello\nDB=postgres\n")
    b = _write(env_dir, "b.env", "KEY=hello\nDB=postgres\n")
    result = _run(["matrix", str(a), str(b), "--no-color"])
    assert result.returncode == 0


def test_matrix_subcommand_exits_one_with_diff(env_dir):
    a = _write(env_dir, "a.env", "KEY=1\n")
    b = _write(env_dir, "b.env", "KEY=2\n")
    result = _run(["matrix", str(a), str(b), "--no-color"])
    assert result.returncode == 1


def test_matrix_subcommand_output_contains_summary(env_dir):
    a = _write(env_dir, "a.env", "KEY=1\n")
    b = _write(env_dir, "b.env", "KEY=1\n")
    result = _run(["matrix", str(a), str(b), "--no-color"])
    assert "envs" in result.stdout
    assert "pairs" in result.stdout


def test_matrix_ignore_values_flag(env_dir):
    a = _write(env_dir, "a.env", "KEY=1\n")
    b = _write(env_dir, "b.env", "KEY=999\n")
    result = _run(["matrix", str(a), str(b), "--no-color", "--ignore-values"])
    assert result.returncode == 0
