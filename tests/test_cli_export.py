"""Integration tests for the 'export' CLI sub-command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.cli_export import add_export_subparser, _run_export


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


class FakeArgs:
    def __init__(self, base, targets, fmt="json", show_values=False, output=None):
        self.base = base
        self.targets = targets
        self.fmt = fmt
        self.show_values = show_values
        self.output = output


def test_export_json_stdout(env_dir, capsys):
    base = write(env_dir / ".env", "KEY=value\nEXTRA=yes\n")
    target = write(env_dir / ".env.staging", "KEY=other\n")
    args = FakeArgs(str(base), [str(target)])
    rc = _run_export(args)
    assert rc == 0
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert any(r["status"] == "mismatch" for r in data)
    assert any(r["status"] == "missing_in_target" for r in data)


def test_export_csv_stdout(env_dir, capsys):
    base = write(env_dir / ".env", "A=1\n")
    target = write(env_dir / ".env.prod", "B=2\n")
    args = FakeArgs(str(base), [str(target)], fmt="csv")
    rc = _run_export(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "key" in out
    assert "status" in out


def test_export_markdown_stdout(env_dir, capsys):
    base = write(env_dir / ".env", "A=1\n")
    target = write(env_dir / ".env.prod", "A=2\n")
    args = FakeArgs(str(base), [str(target)], fmt="markdown")
    rc = _run_export(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "|" in out


def test_export_to_file(env_dir):
    base = write(env_dir / ".env", "X=1\n")
    target = write(env_dir / ".env.staging", "X=2\n")
    out_file = env_dir / "result.json"
    args = FakeArgs(str(base), [str(target)], output=str(out_file))
    rc = _run_export(args)
    assert rc == 0
    data = json.loads(out_file.read_text())
    assert len(data) == 1
    assert data[0]["status"] == "mismatch"


def test_export_show_values(env_dir, capsys):
    base = write(env_dir / ".env", "SECRET=hunter2\n")
    target = write(env_dir / ".env.prod", "SECRET=correct-horse\n")
    args = FakeArgs(str(base), [str(target)], show_values=True)
    rc = _run_export(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    row = data[0]
    assert row["base_value"] == "hunter2"
    assert row["target_value"] == "correct-horse"


def test_export_bad_base_returns_2(env_dir):
    args = FakeArgs(str(env_dir / "nonexistent.env"), [str(env_dir / ".env")])
    rc = _run_export(args)
    assert rc == 2


def test_export_bad_target_returns_2(env_dir):
    base = write(env_dir / ".env", "A=1\n")
    args = FakeArgs(str(base), [str(env_dir / "missing.env")])
    rc = _run_export(args)
    assert rc == 2
