"""Tests for envdiff.patcher."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.patcher import patch_env, PatchResult


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\nKEEP=yes\n")
    return p


def test_patch_updates_existing_key(env_file: Path) -> None:
    result = patch_env(env_file, {"FOO": "newval"})
    assert "FOO" in result.applied
    assert "FOO=newval" in env_file.read_text()


def test_patch_appends_missing_key(env_file: Path) -> None:
    result = patch_env(env_file, {"NEW_KEY": "hello"})
    assert "NEW_KEY" in result.applied
    assert "NEW_KEY=hello" in env_file.read_text()


def test_patch_no_add_skips_missing_key(env_file: Path) -> None:
    result = patch_env(env_file, {"GHOST": "boo"}, add_missing=False)
    assert "GHOST" in result.skipped
    assert "GHOST" not in env_file.read_text()


def test_patch_removes_key(env_file: Path) -> None:
    result = patch_env(env_file, {}, remove_keys=["BAZ"])
    assert "BAZ" in result.removed
    assert "BAZ" not in env_file.read_text()


def test_patch_dry_run_does_not_write(env_file: Path) -> None:
    original = env_file.read_text()
    result = patch_env(env_file, {"FOO": "changed"}, dry_run=True)
    assert "FOO" in result.applied
    assert env_file.read_text() == original


def test_patch_is_clean_when_nothing_changes(env_file: Path) -> None:
    # Skipped keys don't count as changes
    result = patch_env(env_file, {"GHOST": "x"}, add_missing=False)
    assert result.is_clean


def test_patch_result_summary_applied(env_file: Path) -> None:
    result = patch_env(env_file, {"FOO": "v"})
    assert "applied" in result.summary()


def test_patch_result_summary_no_changes(env_file: Path) -> None:
    result = patch_env(env_file, {}, remove_keys=[])
    assert result.summary() == "no changes"


def test_patch_removes_and_updates(env_file: Path) -> None:
    result = patch_env(env_file, {"FOO": "updated"}, remove_keys=["BAZ"])
    text = env_file.read_text()
    assert "FOO=updated" in text
    assert "BAZ" not in text
    assert "KEEP=yes" in text


def test_patch_multiple_updates(env_file: Path) -> None:
    result = patch_env(env_file, {"FOO": "1", "BAZ": "2"})
    text = env_file.read_text()
    assert "FOO=1" in text
    assert "BAZ=2" in text
    assert len(result.applied) == 2
