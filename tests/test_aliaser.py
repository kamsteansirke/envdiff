"""Tests for envdiff.aliaser and envdiff.cli_alias."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.aliaser import AliasGroup, AliasResult, find_aliases
from envdiff.cli_alias import _run_alias, add_alias_subparser


# ---------------------------------------------------------------------------
# Unit tests – find_aliases
# ---------------------------------------------------------------------------

def test_no_aliases_when_all_values_unique():
    env = {"A": "1", "B": "2", "C": "3"}
    result = find_aliases(env)
    assert not result.has_aliases
    assert result.groups == []


def test_detects_simple_alias_pair():
    env = {"DB_URL": "postgres://localhost", "DATABASE_URL": "postgres://localhost", "PORT": "5432"}
    result = find_aliases(env)
    assert result.has_aliases
    assert len(result.groups) == 1
    assert sorted(result.groups[0].keys) == ["DATABASE_URL", "DB_URL"]
    assert result.groups[0].value == "postgres://localhost"


def test_empty_values_ignored_by_default():
    env = {"A": "", "B": "", "C": "real"}
    result = find_aliases(env)
    assert not result.has_aliases


def test_empty_values_included_when_flag_set():
    env = {"A": "", "B": "", "C": "real"}
    result = find_aliases(env, ignore_empty=False)
    assert result.has_aliases
    assert sorted(result.groups[0].keys) == ["A", "B"]


def test_min_group_size_respected():
    env = {"X": "same", "Y": "same", "Z": "same"}
    result_default = find_aliases(env, min_group_size=2)
    assert result_default.has_aliases

    result_large = find_aliases(env, min_group_size=4)
    assert not result_large.has_aliases


def test_total_alias_keys():
    env = {"A": "v", "B": "v", "C": "v"}
    result = find_aliases(env)
    assert result.total_alias_keys == 3


def test_summary_no_aliases():
    result = AliasResult(groups=[])
    assert "No alias" in result.summary()


def test_summary_with_groups():
    group = AliasGroup(value="x", keys=["FOO", "BAR"])
    result = AliasResult(groups=[group])
    summary = result.summary()
    assert "1 alias group" in summary
    assert "FOO" in summary
    assert "BAR" in summary


# ---------------------------------------------------------------------------
# CLI tests – _run_alias / add_alias_subparser
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


class FakeArgs:
    def __init__(self, file: str, include_empty: bool = False, min_group: int = 2, no_color: bool = True):
        self.file = file
        self.include_empty = include_empty
        self.min_group = min_group
        self.no_color = no_color


def test_run_alias_exits_zero_no_aliases(env_dir: Path):
    p = _write(env_dir, ".env", "A=1\nB=2\n")
    rc = _run_alias(FakeArgs(str(p)))
    assert rc == 0


def test_run_alias_exits_one_with_aliases(env_dir: Path):
    p = _write(env_dir, ".env", "A=same\nB=same\n")
    rc = _run_alias(FakeArgs(str(p)))
    assert rc == 1


def test_run_alias_missing_file_exits_two(env_dir: Path):
    rc = _run_alias(FakeArgs(str(env_dir / "missing.env")))
    assert rc == 2


def test_add_alias_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_alias_subparser(sub)
    args = parser.parse_args(["alias", "/dev/null"])
    assert args.func is _run_alias


def test_add_alias_subparser_defaults():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_alias_subparser(sub)
    args = parser.parse_args(["alias", "myfile.env"])
    assert args.min_group == 2
    assert args.include_empty is False
