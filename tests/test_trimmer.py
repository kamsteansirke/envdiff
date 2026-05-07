"""Tests for envdiff.trimmer."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.trimmer import TrimIssue, TrimResult, apply_trim, trim_env


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# TrimIssue / TrimResult helpers
# ---------------------------------------------------------------------------

def test_trim_issue_str() -> None:
    issue = TrimIssue(key="FOO", original=" bar ", trimmed="bar")
    assert "FOO" in str(issue)
    assert "bar" in str(issue)


def test_trim_result_is_clean_when_no_issues(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO=bar\nBAZ=qux\n")
    result = trim_env(p)
    assert result.is_clean


def test_trim_result_not_clean_when_issues(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO= bar \n")
    result = trim_env(p)
    assert not result.is_clean
    assert len(result.issues) == 1
    assert result.issues[0].key == "FOO"


def test_trim_result_summary_clean(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO=bar\n")
    result = trim_env(p)
    assert "no whitespace" in result.summary()


def test_trim_result_summary_with_issues(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO=  bar  \n")
    result = trim_env(p)
    assert "1 key" in result.summary()
    assert "FOO" in result.summary()


# ---------------------------------------------------------------------------
# trim_env detection
# ---------------------------------------------------------------------------

def test_detects_leading_whitespace(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "KEY=  value\n")
    result = trim_env(p)
    assert not result.is_clean
    assert result.cleaned["KEY"] == "value"


def test_detects_trailing_whitespace(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "KEY=value   \n")
    result = trim_env(p)
    assert not result.is_clean
    assert result.cleaned["KEY"] == "value"


def test_no_false_positive_for_clean_value(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "KEY=value\nOTHER=123\n")
    result = trim_env(p)
    assert result.is_clean
    assert result.cleaned == {"KEY": "value", "OTHER": "123"}


def test_multiple_issues_detected(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "A= 1 \nB=clean\nC=  3\n")
    result = trim_env(p)
    assert len(result.issues) == 2
    keys = {i.key for i in result.issues}
    assert keys == {"A", "C"}


# ---------------------------------------------------------------------------
# apply_trim (in-place fix)
# ---------------------------------------------------------------------------

def test_apply_trim_rewrites_file(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO=  bar  \nBAZ=qux\n")
    result = trim_env(p)
    changed = apply_trim(p, result)
    assert len(changed) == 1
    content = p.read_text(encoding="utf-8")
    assert "FOO=bar" in content
    assert "BAZ=qux" in content


def test_apply_trim_no_changes_when_clean(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO=bar\n")
    result = trim_env(p)
    changed = apply_trim(p, result)
    assert changed == []
    assert p.read_text(encoding="utf-8") == "FOO=bar\n"


def test_apply_trim_preserves_comments(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "# comment\nFOO=  bar\n")
    result = trim_env(p)
    apply_trim(p, result)
    content = p.read_text(encoding="utf-8")
    assert "# comment" in content
