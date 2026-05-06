"""Tests for envdiff.baseline."""
import json
import os
import pytest

from envdiff.baseline import (
    BaselineError,
    Baseline,
    capture_baseline,
    save_baseline,
    load_baseline,
    diff_against_baseline,
)


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(p, content):
    p.write_text(content, encoding="utf-8")
    return str(p)


def test_capture_baseline_reads_keys(env_dir):
    path = _write(env_dir / ".env", "FOO=bar\nBAZ=qux\n")
    bl = capture_baseline(path)
    assert bl.keys == {"FOO": "bar", "BAZ": "qux"}
    assert bl.source == os.path.abspath(path)
    assert bl.captured_at  # non-empty ISO timestamp


def test_save_and_load_roundtrip(env_dir):
    path = _write(env_dir / ".env", "KEY=value\n")
    bl = capture_baseline(path)
    out = str(env_dir / "baseline.json")
    save_baseline(bl, out)
    loaded = load_baseline(out)
    assert loaded.keys == bl.keys
    assert loaded.source == bl.source
    assert loaded.captured_at == bl.captured_at


def test_load_baseline_missing_file_raises(env_dir):
    with pytest.raises(BaselineError, match="Cannot load baseline"):
        load_baseline(str(env_dir / "nonexistent.json"))


def test_load_baseline_bad_json_raises(env_dir):
    bad = env_dir / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    with pytest.raises(BaselineError):
        load_baseline(str(bad))


def test_diff_no_drift():
    bl = Baseline(source="x", captured_at="t", keys={"A": "1", "B": "2"})
    result = diff_against_baseline(bl, {"A": "1", "B": "2"})
    assert result == {"added": {}, "removed": {}, "changed": {}}


def test_diff_detects_added():
    bl = Baseline(source="x", captured_at="t", keys={"A": "1"})
    result = diff_against_baseline(bl, {"A": "1", "NEW": "val"})
    assert result["added"] == {"NEW": "val"}


def test_diff_detects_removed():
    bl = Baseline(source="x", captured_at="t", keys={"A": "1", "OLD": "gone"})
    result = diff_against_baseline(bl, {"A": "1"})
    assert result["removed"] == {"OLD": "gone"}


def test_diff_detects_changed():
    bl = Baseline(source="x", captured_at="t", keys={"A": "old"})
    result = diff_against_baseline(bl, {"A": "new"})
    assert result["changed"] == {"A": {"baseline": "old", "current": "new"}}


def test_baseline_to_dict_and_from_dict():
    bl = Baseline(source="/a/.env", captured_at="2024-01-01T00:00:00+00:00", keys={"X": "1"})
    d = bl.to_dict()
    assert d["source"] == "/a/.env"
    restored = Baseline.from_dict(d)
    assert restored.keys == {"X": "1"}
