"""Tests for envdiff.linter."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.linter import lint_env, LintIssue, LintResult


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


def test_clean_file_passes(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "APP_NAME=myapp\nDEBUG=true\n")
    result = lint_env(p)
    assert result.passed
    assert "OK" in result.summary()


def test_lowercase_key_triggers_w002(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "app_name=myapp\n")
    result = lint_env(p, require_uppercase=True)
    assert not result.passed
    codes = [i.code for i in result.issues]
    assert "W002" in codes


def test_require_uppercase_disabled(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "app_name=myapp\n")
    result = lint_env(p, require_uppercase=False)
    assert result.passed


def test_empty_value_allowed_by_default(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "SECRET=\n")
    result = lint_env(p, forbid_empty_values=False)
    assert result.passed


def test_empty_value_forbidden(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "SECRET=\n")
    result = lint_env(p, forbid_empty_values=True)
    assert not result.passed
    codes = [i.code for i in result.issues]
    assert "W003" in codes


def test_unreadable_file_returns_e000(env_dir: Path) -> None:
    missing = env_dir / "nonexistent.env"
    result = lint_env(missing)
    assert not result.passed
    assert result.issues[0].code == "E000"


def test_summary_lists_issues(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "lower=val\nSECRET=\n")
    result = lint_env(p, require_uppercase=True, forbid_empty_values=True)
    summary = result.summary()
    assert str(p) in summary
    assert "issue" in summary


def test_lint_issue_str() -> None:
    issue = LintIssue(line_no=3, key="foo", code="W002",
                      message="Key should be UPPER_SNAKE_CASE")
    text = str(issue)
    assert "line 3" in text
    assert "W002" in text
    assert "foo" in text


def test_multiple_issues_in_one_file(env_dir: Path) -> None:
    content = "lower=\nANOTHER_lower=val\n"
    p = _write(env_dir, ".env", content)
    result = lint_env(p, require_uppercase=True, forbid_empty_values=True)
    codes = [i.code for i in result.issues]
    assert "W002" in codes
    assert "W003" in codes
    assert len(result.issues) >= 2
