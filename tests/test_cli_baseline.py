"""Tests for envdiff.cli_baseline."""
import argparse
import json
import pytest

from envdiff.cli_baseline import add_baseline_subparser, _run_capture, _run_check


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(p, content):
    p.write_text(content, encoding="utf-8")
    return str(p)


class FakeArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_add_baseline_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="cmd")
    add_baseline_subparser(subs)
    parsed = parser.parse_args(["baseline", "capture", ".env"])
    assert parsed.baseline_cmd == "capture"


def test_run_capture_creates_file(env_dir):
    env = _write(env_dir / ".env", "FOO=bar\n")
    out = str(env_dir / "bl.json")
    args = FakeArgs(env_file=env, output=out)
    rc = _run_capture(args)
    assert rc == 0
    data = json.loads((env_dir / "bl.json").read_text())
    assert data["keys"] == {"FOO": "bar"}


def test_run_capture_bad_file_returns_2(env_dir):
    args = FakeArgs(env_file=str(env_dir / "missing.env"), output=str(env_dir / "bl.json"))
    rc = _run_capture(args)
    assert rc == 2


def test_run_check_no_drift(env_dir):
    env = _write(env_dir / ".env", "FOO=bar\n")
    bl_path = str(env_dir / "bl.json")
    _run_capture(FakeArgs(env_file=env, output=bl_path))
    args = FakeArgs(env_file=env, baseline=bl_path, as_json=False)
    rc = _run_check(args)
    assert rc == 0


def test_run_check_detects_drift(env_dir):
    env = _write(env_dir / ".env", "FOO=bar\n")
    bl_path = str(env_dir / "bl.json")
    _run_capture(FakeArgs(env_file=env, output=bl_path))
    _write(env_dir / ".env", "FOO=changed\nNEW=key\n")
    args = FakeArgs(env_file=str(env_dir / ".env"), baseline=bl_path, as_json=False)
    rc = _run_check(args)
    assert rc == 1


def test_run_check_json_output(env_dir, capsys):
    env = _write(env_dir / ".env", "A=1\n")
    bl_path = str(env_dir / "bl.json")
    _run_capture(FakeArgs(env_file=env, output=bl_path))
    _write(env_dir / ".env", "A=2\n")
    args = FakeArgs(env_file=str(env_dir / ".env"), baseline=bl_path, as_json=True)
    _run_check(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "changed" in data
    assert "A" in data["changed"]


def test_run_check_missing_baseline_returns_2(env_dir):
    env = _write(env_dir / ".env", "A=1\n")
    args = FakeArgs(env_file=env, baseline=str(env_dir / "nope.json"), as_json=False)
    rc = _run_check(args)
    assert rc == 2
