"""Integration tests: cli_profile wired into the main CLI entry point."""
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def _run(*args):
    return subprocess.run(
        [sys.executable, "-m", "envdiff", *args],
        capture_output=True,
        text=True,
    )


def test_profile_subcommand_exits_zero(env_dir):
    p = _write(env_dir, ".env", "PORT=8080\nDEBUG=true\n")
    result = _run("profile", str(p))
    assert result.returncode == 0


def test_profile_subcommand_output(env_dir):
    p = _write(env_dir, ".env", "PORT=8080\nSECRET_KEY=s3cr3t\n")
    result = _run("profile", str(p))
    assert "Total keys" in result.stdout
    assert "Secret keys" in result.stdout


def test_profile_subcommand_show_keys(env_dir):
    p = _write(env_dir, ".env", "API_KEY=xyz\nHOST=localhost\n")
    result = _run("profile", "--show-keys", str(p))
    assert "API_KEY" in result.stdout


def test_profile_missing_file_exits_nonzero(env_dir):
    result = _run("profile", str(env_dir / "ghost.env"))
    assert result.returncode != 0
