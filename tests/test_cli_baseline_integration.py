"""Integration tests for the baseline subcommand via CLI entry point."""
import json
import subprocess
import sys
import pytest


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(p, content):
    p.write_text(content, encoding="utf-8")
    return str(p)


def _run(*args):
    return subprocess.run(
        [sys.executable, "-m", "envdiff"] + list(args),
        capture_output=True,
        text=True,
    )


def test_baseline_capture_exits_zero(env_dir):
    env = _write(env_dir / ".env", "KEY=val\n")
    bl = str(env_dir / "bl.json")
    result = _run("baseline", "capture", env, "-o", bl)
    assert result.returncode == 0
    assert "bl.json" in result.stdout


def test_baseline_check_no_drift_exits_zero(env_dir):
    env = _write(env_dir / ".env", "KEY=val\n")
    bl = str(env_dir / "bl.json")
    _run("baseline", "capture", env, "-o", bl)
    result = _run("baseline", "check", env, "-b", bl)
    assert result.returncode == 0


def test_baseline_check_drift_exits_one(env_dir):
    env = _write(env_dir / ".env", "KEY=val\n")
    bl = str(env_dir / "bl.json")
    _run("baseline", "capture", env, "-o", bl)
    _write(env_dir / ".env", "KEY=changed\n")
    result = _run("baseline", "check", str(env_dir / ".env"), "-b", bl)
    assert result.returncode == 1
    assert "KEY" in result.stdout
