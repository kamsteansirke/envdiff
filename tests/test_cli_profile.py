"""Tests for envdiff.cli_profile."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from envdiff.cli_profile import add_profile_subparser, _run_profile


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def _make_args(files, show_keys=False):
    return SimpleNamespace(files=[str(f) for f in files], show_keys=show_keys)


def test_add_profile_subparser_registers_command():
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_profile_subparser(sub)
    args = parser.parse_args(["profile", "/tmp/x.env"])
    assert args.func is _run_profile


def test_run_profile_exit_zero(env_dir, capsys):
    p = _write(env_dir, ".env", "PORT=8080\nSECRET_KEY=abc\n")
    code = _run_profile(_make_args([p]))
    assert code == 0


def test_run_profile_output_contains_summary(env_dir, capsys):
    p = _write(env_dir, ".env", "A=1\nB=2\n")
    _run_profile(_make_args([p]))
    out = capsys.readouterr().out
    assert "Total keys" in out
    assert "2" in out


def test_run_profile_show_keys(env_dir, capsys):
    p = _write(env_dir, ".env", "SECRET_KEY=abc\nPORT=3000\n")
    _run_profile(_make_args([p], show_keys=True))
    out = capsys.readouterr().out
    assert "SECRET_KEY" in out
    assert "PORT" in out


def test_run_profile_missing_file_returns_1(env_dir, capsys):
    code = _run_profile(_make_args([env_dir / "nonexistent.env"]))
    assert code == 1
    err = capsys.readouterr().err
    assert "ERROR" in err


def test_run_profile_multiple_files(env_dir, capsys):
    p1 = _write(env_dir, "a.env", "X=1\n")
    p2 = _write(env_dir, "b.env", "Y=2\nZ=3\n")
    code = _run_profile(_make_args([p1, p2]))
    out = capsys.readouterr().out
    assert code == 0
    assert "a.env" in out
    assert "b.env" in out
