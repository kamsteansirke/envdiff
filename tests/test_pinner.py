"""Tests for envdiff.pinner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.pinner import (
    PinEntry,
    PinError,
    PinResult,
    check_pin,
    create_pin,
    load_pin,
    save_pin,
)


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


def test_create_pin_returns_all_keys(env_dir):
    f = _write(env_dir / ".env", "FOO=bar\nBAZ=qux\n")
    entries = create_pin(f)
    assert set(entries.keys()) == {"FOO", "BAZ"}


def test_create_pin_no_value_hash_by_default(env_dir):
    f = _write(env_dir / ".env", "FOO=bar\n")
    entries = create_pin(f)
    assert entries["FOO"].value_hash == ""


def test_create_pin_with_values_stores_hash(env_dir):
    f = _write(env_dir / ".env", "FOO=bar\n")
    entries = create_pin(f, pin_values=True)
    assert len(entries["FOO"].value_hash) == 64  # sha256 hex


def test_save_and_load_roundtrip(env_dir):
    f = _write(env_dir / ".env", "FOO=bar\nBAZ=qux\n")
    pin_path = env_dir / ".envpin"
    entries = create_pin(f, pin_values=True)
    save_pin(entries, pin_path)
    loaded = load_pin(pin_path)
    assert set(loaded.keys()) == {"FOO", "BAZ"}
    assert loaded["FOO"].value_hash == entries["FOO"].value_hash


def test_load_pin_missing_file_raises(env_dir):
    with pytest.raises(PinError, match="not found"):
        load_pin(env_dir / "nonexistent.envpin")


def test_load_pin_malformed_json_raises(env_dir):
    bad = env_dir / ".envpin"
    bad.write_text("not json", encoding="utf-8")
    with pytest.raises(PinError, match="Malformed"):
        load_pin(bad)


def test_check_pin_clean_when_unchanged(env_dir):
    f = _write(env_dir / ".env", "FOO=bar\n")
    pin_path = env_dir / ".envpin"
    save_pin(create_pin(f), pin_path)
    result = check_pin(f, pin_path)
    assert result.is_clean
    assert result.summary() == "No drift detected."


def test_check_pin_detects_added_key(env_dir):
    pin_path = env_dir / ".envpin"
    save_pin(create_pin(_write(env_dir / ".env", "FOO=bar\n")), pin_path)
    _write(env_dir / ".env", "FOO=bar\nNEW=val\n")
    result = check_pin(env_dir / ".env", pin_path)
    assert "NEW" in result.added
    assert not result.is_clean


def test_check_pin_detects_removed_key(env_dir):
    pin_path = env_dir / ".envpin"
    save_pin(create_pin(_write(env_dir / ".env", "FOO=bar\nOLD=x\n")), pin_path)
    _write(env_dir / ".env", "FOO=bar\n")
    result = check_pin(env_dir / ".env", pin_path)
    assert "OLD" in result.removed


def test_check_pin_detects_value_change(env_dir):
    pin_path = env_dir / ".envpin"
    save_pin(create_pin(_write(env_dir / ".env", "FOO=bar\n"), pin_values=True), pin_path)
    _write(env_dir / ".env", "FOO=changed\n")
    result = check_pin(env_dir / ".env", pin_path, pin_values=True)
    assert "FOO" in result.changed


def test_pin_result_summary_lists_counts(env_dir):
    r = PinResult(added=["A"], removed=["B", "C"], changed=["D"])
    s = r.summary()
    assert "1 added" in s
    assert "2 removed" in s
    assert "1 changed" in s
