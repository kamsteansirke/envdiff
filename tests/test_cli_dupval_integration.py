"""Integration tests for the `envdiff dupval` CLI sub-command."""
from __future__ import annotations

import subprocess
import sys
import pytest


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(directory, name: str, content: str) -> str:
    p = directory / name
    p.write_text(content)
    return str(p)


def _run(*args: str) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
    return subprocess.run(
        [sys.executable, "-m", "envdiff", *args],
        capture_output=True,
        text=True,
    )


def test_dupval_subcommand_exits_zero_no_duplicates(env_dir):
    path = _write(env_dir, ".env", "A=alpha\nB=beta\n")
    result = _run("dupval", path)
    assert result.returncode == 0


def test_dupval_subcommand_exits_one_with_duplicates(env_dir):
    path = _write(env_dir, ".env", "A=same\nB=same\n")
    result = _run("dupval", path)
    assert result.returncode == 1


def test_dupval_subcommand_output_mentions_key(env_dir):
    path = _write(env_dir, ".env", "FOO=shared\nBAR=shared\n")
    result = _run("dupval", path)
    assert "FOO" in result.stdout or "BAR" in result.stdout
