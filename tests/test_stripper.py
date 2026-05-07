"""Tests for envdiff.stripper."""
from __future__ import annotations

import pytest
from pathlib import Path

from envdiff.stripper import strip_env, StripIssue, StripResult


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


def test_clean_file_is_clean(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO=bar\nBAZ=qux\n")
    result = strip_env(p)
    assert result.is_clean
    assert result.issues == []


def test_blank_line_detected(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "FOO=bar\n\nBAZ=qux\n")
    result = strip_env(p)
    assert not result.is_clean
    assert len(result.issues) == 1
    assert result.issues[0].reason == "blank"
    assert result.issues[0].line_number == 2


def test_comment_line_detected(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "# this is a comment\nFOO=bar\n")
    result = strip_env(p)
    assert not result.is_clean
    assert result.issues[0].reason == "comment"
    assert result.issues[0].line_number == 1


def test_multiple_issues_counted(env_dir: Path) -> None:
    content = "# header\n\nFOO=bar\n# another\nBAZ=qux\n"
    p = _write(env_dir, ".env", content)
    result = strip_env(p)
    assert len(result.issues) == 3
    reasons = [i.reason for i in result.issues]
    assert reasons.count("comment") == 2
    assert reasons.count("blank") == 1


def test_cleaned_contains_only_kv(env_dir: Path) -> None:
    content = "# header\n\nFOO=bar\nBAZ=qux\n"
    p = _write(env_dir, ".env", content)
    result = strip_env(p)
    assert result.cleaned == {"FOO": "bar", "BAZ": "qux"}


def test_render_produces_valid_env(env_dir: Path) -> None:
    content = "# comment\nFOO=bar\n\nBAZ=hello world\n"
    p = _write(env_dir, ".env", content)
    result = strip_env(p)
    rendered = result.render()
    assert "FOO=bar" in rendered
    assert 'BAZ="hello world"' in rendered
    assert "#" not in rendered


def test_summary_clean(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "A=1\n")
    result = strip_env(p)
    assert "no strippable" in result.summary()


def test_summary_with_issues(env_dir: Path) -> None:
    content = "# top\n\nFOO=1\n"
    p = _write(env_dir, ".env", content)
    result = strip_env(p)
    s = result.summary()
    assert "2 strippable" in s
    assert "blank" in s
    assert "comment" in s


def test_strip_issue_str() -> None:
    issue = StripIssue(line_number=3, original="  ", reason="blank")
    assert "L3" in str(issue)
    assert "blank" in str(issue)
