"""Integration tests for the 'envdiff patch' CLI subcommand."""
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


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "envdiff", *args],
        capture_output=True,
        text=True,
    )


def test_patch_subcommand_exits_zero(env_dir: Path) -> None:
    f = _write(env_dir, ".env", "FOO=bar\n")
    result = _run("patch", str(f), "FOO=baz")
    assert result.returncode == 0


def test_patch_subcommand_output_contains_applied(env_dir: Path) -> None:
    f = _write(env_dir, ".env", "FOO=bar\n")
    result = _run("patch", str(f), "FOO=new")
    assert "applied" in result.stdout


def test_patch_subcommand_dry_run_no_write(env_dir: Path) -> None:
    f = _write(env_dir, ".env", "FOO=original\n")
    _run("patch", str(f), "FOO=changed", "--dry-run")
    assert "FOO=original" in f.read_text()
