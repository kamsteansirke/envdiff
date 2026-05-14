"""Tests for envdiff.cli_extract."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.cli_extract import add_extract_subparser, _run_extract


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


class FakeArgs:
    def __init__(
        self,
        file: Path,
        keys: list | None = None,
        patterns: list | None = None,
        invert: bool = False,
        output: Path | None = None,
    ) -> None:
        self.file = file
        self.keys = keys or []
        self.patterns = patterns or []
        self.invert = invert
        self.output = output


def test_add_extract_subparser_registers_command() -> None:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_extract_subparser(subs)
    args = parser.parse_args(["extract", "/dev/null"])
    assert hasattr(args, "func")


def test_run_extract_exits_zero(env_dir: Path, capsys: pytest.CaptureFixture) -> None:
    f = _write(env_dir / ".env", "A=1\nB=2\n")
    args = FakeArgs(file=f)
    rc = _run_extract(args)
    assert rc == 0


def test_run_extract_stdout_contains_key(env_dir: Path, capsys: pytest.CaptureFixture) -> None:
    f = _write(env_dir / ".env", "HELLO=world\n")
    args = FakeArgs(file=f)
    _run_extract(args)
    out = capsys.readouterr().out
    assert "HELLO=world" in out


def test_run_extract_filter_by_key(env_dir: Path, capsys: pytest.CaptureFixture) -> None:
    f = _write(env_dir / ".env", "A=1\nB=2\n")
    args = FakeArgs(file=f, keys=["A"])
    _run_extract(args)
    out = capsys.readouterr().out
    assert "A=1" in out
    assert "B=" not in out


def test_run_extract_writes_to_output_file(env_dir: Path, capsys: pytest.CaptureFixture) -> None:
    f = _write(env_dir / ".env", "X=42\nY=99\n")
    out_file = env_dir / "out.env"
    args = FakeArgs(file=f, keys=["X"], output=out_file)
    rc = _run_extract(args)
    assert rc == 0
    assert out_file.exists()
    content = out_file.read_text()
    assert "X=42" in content
    assert "Y=" not in content


def test_run_extract_invert(env_dir: Path, capsys: pytest.CaptureFixture) -> None:
    f = _write(env_dir / ".env", "DB_HOST=h\nAPP_NAME=n\n")
    args = FakeArgs(file=f, patterns=[r"^DB_"], invert=True)
    _run_extract(args)
    out = capsys.readouterr().out
    assert "APP_NAME=n" in out
    assert "DB_HOST" not in out
