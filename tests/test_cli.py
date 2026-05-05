"""Tests for envdiff.cli."""

import pytest
from pathlib import Path
from envdiff.cli import main


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_cli_no_differences(env_dir, capsys):
    base = write(env_dir / ".env.base", "KEY=value\nFOO=bar\n")
    target = write(env_dir / ".env.prod", "KEY=value\nFOO=bar\n")
    rc = main([str(base), str(target), "--no-color"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "No differences" in out


def test_cli_missing_key_returns_1(env_dir, capsys):
    base = write(env_dir / ".env.base", "KEY=value\nSECRET=abc\n")
    target = write(env_dir / ".env.prod", "KEY=value\n")
    rc = main([str(base), str(target), "--no-color"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "SECRET" in out


def test_cli_mismatch_detected(env_dir, capsys):
    base = write(env_dir / ".env.base", "KEY=original\n")
    target = write(env_dir / ".env.prod", "KEY=changed\n")
    rc = main([str(base), str(target), "--no-color"])
    assert rc == 1
    assert "MISMATCH" in capsys.readouterr().out


def test_cli_show_values(env_dir, capsys):
    base = write(env_dir / ".env.base", "KEY=original\n")
    target = write(env_dir / ".env.prod", "KEY=changed\n")
    main([str(base), str(target), "--no-color", "--show-values"])
    out = capsys.readouterr().out
    assert "original" in out
    assert "changed" in out


def test_cli_ignore_values(env_dir, capsys):
    base = write(env_dir / ".env.base", "KEY=original\n")
    target = write(env_dir / ".env.prod", "KEY=changed\n")
    rc = main([str(base), str(target), "--no-color", "--ignore-values"])
    assert rc == 0


def test_cli_multiple_targets(env_dir, capsys):
    base = write(env_dir / ".env.base", "A=1\nB=2\n")
    t1 = write(env_dir / ".env.staging", "A=1\nB=2\n")
    t2 = write(env_dir / ".env.prod", "A=1\n")
    rc = main([str(base), str(t1), str(t2), "--no-color"])
    assert rc == 1
    out = capsys.readouterr().out
    assert ".env.staging" in out or "staging" in out
    assert "B" in out


def test_cli_bad_base_file(env_dir, capsys):
    rc = main([str(env_dir / "nonexistent.env"), str(env_dir / "other.env")])
    assert rc == 2
    assert "Error" in capsys.readouterr().err
