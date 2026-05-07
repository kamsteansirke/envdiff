"""Integration tests for the 'pin' CLI subcommand."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


def _run(*args: str) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
    return subprocess.run(
        [sys.executable, "-m", "envdiff", *args],
        capture_output=True,
        text=True,
    )


def test_pin_capture_exits_zero(env_dir):
    env = _write(env_dir / ".env", "FOO=bar\nBAZ=qux\n")
    pin = env_dir / ".envpin"
    result = _run("pin", "capture", str(env), "--pin-file", str(pin))
    assert result.returncode == 0
    assert "Pinned" in result.stdout


def test_pin_check_no_drift_exits_zero(env_dir):
    env = _write(env_dir / ".env", "FOO=bar\n")
    pin = env_dir / ".envpin"
    _run("pin", "capture", str(env), "--pin-file", str(pin))
    result = _run("pin", "check", str(env), "--pin-file", str(pin))
    assert result.returncode == 0
    assert "No drift" in result.stdout


def test_pin_check_drift_exits_one(env_dir):
    env = _write(env_dir / ".env", "FOO=bar\n")
    pin = env_dir / ".envpin"
    _run("pin", "capture", str(env), "--pin-file", str(pin))
    _write(env_dir / ".env", "FOO=bar\nEXTRA=1\n")
    result = _run("pin", "check", str(env), "--pin-file", str(pin))
    assert result.returncode == 1
    assert "EXTRA" in result.stdout
