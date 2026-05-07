"""Tests for envdiff.cli_pin."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.cli_pin import _run_capture, _run_check, add_pin_subparser


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


class FakeArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_add_pin_subparser_registers_command():
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    add_pin_subparser(sub)
    ns = root.parse_args(["pin", "capture", "myfile.env"])
    assert ns.cmd == "pin"


def test_run_capture_creates_pin_file(env_dir):
    env = _write(env_dir / ".env", "FOO=bar\n")
    pin = env_dir / ".envpin"
    args = FakeArgs(env_file=str(env), pin_file=str(pin), pin_values=False)
    rc = _run_capture(args)
    assert rc == 0
    assert pin.exists()


def test_run_capture_missing_env_returns_1(env_dir):
    args = FakeArgs(
        env_file=str(env_dir / "missing.env"),
        pin_file=str(env_dir / ".envpin"),
        pin_values=False,
    )
    rc = _run_capture(args)
    assert rc == 1


def test_run_check_clean_returns_0(env_dir):
    env = _write(env_dir / ".env", "FOO=bar\n")
    pin = env_dir / ".envpin"
    _run_capture(FakeArgs(env_file=str(env), pin_file=str(pin), pin_values=False))
    rc = _run_check(FakeArgs(env_file=str(env), pin_file=str(pin), pin_values=False))
    assert rc == 0


def test_run_check_drift_returns_1(env_dir):
    env = _write(env_dir / ".env", "FOO=bar\n")
    pin = env_dir / ".envpin"
    _run_capture(FakeArgs(env_file=str(env), pin_file=str(pin), pin_values=False))
    _write(env_dir / ".env", "FOO=bar\nNEW=val\n")
    rc = _run_check(FakeArgs(env_file=str(env), pin_file=str(pin), pin_values=False))
    assert rc == 1


def test_run_check_missing_pin_returns_1(env_dir):
    env = _write(env_dir / ".env", "FOO=bar\n")
    args = FakeArgs(
        env_file=str(env),
        pin_file=str(env_dir / "nonexistent.envpin"),
        pin_values=False,
    )
    rc = _run_check(args)
    assert rc == 1
