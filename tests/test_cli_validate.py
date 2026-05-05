"""Tests for envdiff.cli_validate."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from envdiff.cli_validate import add_validate_subparser, _run_validate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _make_args(schema: str, envfiles: list, no_color: bool = True) -> SimpleNamespace:
    return SimpleNamespace(schema=schema, envfiles=envfiles, no_color=no_color)


# ---------------------------------------------------------------------------
# Subparser registration
# ---------------------------------------------------------------------------

def test_add_validate_subparser_registers_command():
    import argparse
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    add_validate_subparser(sub)
    args = root.parse_args(["validate", "--schema", "s.json", ".env"])
    assert args.envfiles == [".env"]
    assert args.schema == "s.json"


# ---------------------------------------------------------------------------
# _run_validate
# ---------------------------------------------------------------------------

class TestRunValidate:
    def test_valid_env_returns_0(self, env_dir: Path, capsys):
        schema_file = _write(
            env_dir / "schema.json",
            json.dumps({"PORT": {"required": True, "pattern": r"\d+"}}),
        )
        env_file = _write(env_dir / ".env", "PORT=8080\n")
        args = _make_args(str(schema_file), [str(env_file)])
        assert _run_validate(args) == 0
        out = capsys.readouterr().out
        assert "OK" in out or "✓" in out

    def test_missing_key_returns_1(self, env_dir: Path, capsys):
        schema_file = _write(
            env_dir / "schema.json",
            json.dumps({"SECRET": {"required": True}}),
        )
        env_file = _write(env_dir / ".env", "PORT=8080\n")
        args = _make_args(str(schema_file), [str(env_file)])
        assert _run_validate(args) == 1
        out = capsys.readouterr().out
        assert "SECRET" in out

    def test_pattern_violation_returns_1(self, env_dir: Path, capsys):
        schema_file = _write(
            env_dir / "schema.json",
            json.dumps({"PORT": {"pattern": r"\d+"}}),
        )
        env_file = _write(env_dir / ".env", "PORT=not-a-port\n")
        args = _make_args(str(schema_file), [str(env_file)])
        assert _run_validate(args) == 1

    def test_bad_schema_returns_2(self, env_dir: Path, capsys):
        bad_schema = _write(env_dir / "bad.json", "[1,2,3]")
        env_file = _write(env_dir / ".env", "X=1\n")
        args = _make_args(str(bad_schema), [str(env_file)])
        assert _run_validate(args) == 2

    def test_multiple_files_all_valid(self, env_dir: Path):
        schema_file = _write(
            env_dir / "schema.json",
            json.dumps({"KEY": {}}),
        )
        f1 = _write(env_dir / ".env", "KEY=a\n")
        f2 = _write(env_dir / ".env.prod", "KEY=b\n")
        args = _make_args(str(schema_file), [str(f1), str(f2)])
        assert _run_validate(args) == 0

    def test_multiple_files_one_invalid(self, env_dir: Path):
        schema_file = _write(
            env_dir / "schema.json",
            json.dumps({"KEY": {"required": True}}),
        )
        f1 = _write(env_dir / ".env", "KEY=a\n")
        f2 = _write(env_dir / ".env.prod", "OTHER=b\n")
        args = _make_args(str(schema_file), [str(f1), str(f2)])
        assert _run_validate(args) == 1
