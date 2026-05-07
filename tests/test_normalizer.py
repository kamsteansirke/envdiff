"""Tests for envdiff.normalizer."""
from __future__ import annotations

import pathlib

import pytest

from envdiff.normalizer import (
    CasePolicy,
    NormalizeOptions,
    normalize_env,
    render_normalized,
)


@pytest.fixture()
def env_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path


def _write(directory: pathlib.Path, name: str, content: str) -> pathlib.Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


def test_clean_file_is_clean(env_dir):
    p = _write(env_dir, ".env", "ALPHA=1\nBETA=2\n")
    result = normalize_env(str(p))
    assert result.is_clean


def test_sort_keys_reorders(env_dir):
    p = _write(env_dir, ".env", "ZEBRA=z\nAPPLE=a\n")
    result = normalize_env(str(p), NormalizeOptions(sort_keys=True))
    assert list(result.normalized.keys()) == ["APPLE", "ZEBRA"]
    assert any("reordered" in c for c in result.changes)


def test_no_sort_preserves_order(env_dir):
    p = _write(env_dir, ".env", "ZEBRA=z\nAPPLE=a\n")
    result = normalize_env(str(p), NormalizeOptions(sort_keys=False))
    assert list(result.normalized.keys()) == ["ZEBRA", "APPLE"]


def test_case_upper_renames_keys(env_dir):
    p = _write(env_dir, ".env", "my_key=hello\n")
    result = normalize_env(str(p), NormalizeOptions(case_policy=CasePolicy.UPPER, sort_keys=False))
    assert "MY_KEY" in result.normalized
    assert "my_key" not in result.normalized
    assert any("MY_KEY" in c for c in result.changes)


def test_case_lower_renames_keys(env_dir):
    p = _write(env_dir, ".env", "MY_KEY=hello\n")
    result = normalize_env(str(p), NormalizeOptions(case_policy=CasePolicy.LOWER, sort_keys=False))
    assert "my_key" in result.normalized
    assert "MY_KEY" not in result.normalized


def test_strip_empty_values_removes_key(env_dir):
    p = _write(env_dir, ".env", "PRESENT=yes\nEMPTY=\n")
    result = normalize_env(str(p), NormalizeOptions(strip_empty_values=True, sort_keys=False))
    assert "EMPTY" not in result.normalized
    assert "PRESENT" in result.normalized
    assert any("EMPTY" in c for c in result.changes)


def test_strip_empty_values_false_keeps_key(env_dir):
    p = _write(env_dir, ".env", "EMPTY=\n")
    result = normalize_env(str(p), NormalizeOptions(strip_empty_values=False))
    assert "EMPTY" in result.normalized


def test_render_normalized_produces_env_format(env_dir):
    p = _write(env_dir, ".env", "B=2\nA=1\n")
    result = normalize_env(str(p))
    rendered = render_normalized(result)
    assert "A=1" in rendered
    assert "B=2" in rendered
    assert rendered.endswith("\n")


def test_summary_clean(env_dir):
    p = _write(env_dir, ".env", "A=1\n")
    result = normalize_env(str(p))
    assert "No normalization" in result.summary()


def test_summary_with_changes(env_dir):
    p = _write(env_dir, ".env", "b=2\na=1\n")
    result = normalize_env(str(p), NormalizeOptions(case_policy=CasePolicy.UPPER))
    summary = result.summary()
    assert "change" in summary
