"""Tests for envdiff.sanitizer."""
import pytest
from envdiff.sanitizer import SanitizeIssue, SanitizeResult, sanitize_env


def test_clean_env_is_clean():
    result = sanitize_env({"HOST": "localhost", "PORT": "5432"})
    assert result.is_clean
    assert result.sanitized == {"HOST": "localhost", "PORT": "5432"}


def test_trailing_whitespace_detected():
    result = sanitize_env({"KEY": "value   "})
    assert not result.is_clean
    assert len(result.issues) == 1
    assert result.issues[0].key == "KEY"
    assert "trailing whitespace" in result.issues[0].reason
    assert result.sanitized["KEY"] == "value"


def test_trailing_whitespace_tab_detected():
    result = sanitize_env({"KEY": "value\t"})
    assert not result.is_clean
    assert result.sanitized["KEY"] == "value"


def test_control_char_detected():
    result = sanitize_env({"KEY": "val\x1bue"})
    assert not result.is_clean
    assert "control characters" in result.issues[0].reason
    assert result.sanitized["KEY"] == "value"


def test_null_byte_detected():
    result = sanitize_env({"KEY": "val\x00ue"})
    assert not result.is_clean
    assert "null byte" in result.issues[0].reason
    assert result.sanitized["KEY"] == "value"


def test_null_byte_and_trailing_whitespace_two_issues():
    result = sanitize_env({"KEY": "val\x00ue  "})
    assert len(result.issues) == 2
    assert result.sanitized["KEY"] == "value"


def test_fix_trailing_whitespace_disabled():
    result = sanitize_env({"KEY": "value   "}, fix_trailing_whitespace=False)
    assert result.is_clean
    assert result.sanitized["KEY"] == "value   "


def test_fix_control_chars_disabled():
    result = sanitize_env({"KEY": "val\x1bue"}, fix_control_chars=False)
    assert result.is_clean
    assert result.sanitized["KEY"] == "val\x1bue"


def test_strip_null_bytes_disabled():
    result = sanitize_env({"KEY": "val\x00ue"}, strip_null_bytes=False)
    # control-char pass also skips \x00 when strip_null_bytes off but
    # \x00 IS matched by _CONTROL_RE (\x00-\x08), so only control issue fires
    assert result.sanitized["KEY"] == "value"


def test_empty_env_is_clean():
    result = sanitize_env({})
    assert result.is_clean
    assert result.sanitized == {}


def test_issue_str_with_fix():
    issue = SanitizeIssue("KEY", "null byte removed", "val\x00", "val")
    assert "KEY" in str(issue)
    assert "null byte removed" in str(issue)
    assert "->" in str(issue)


def test_issue_str_without_fix():
    issue = SanitizeIssue("KEY", "some reason", "original")
    assert "->" not in str(issue)


def test_summary_clean():
    result = sanitize_env({"A": "ok"})
    assert "No sanitization" in result.summary()


def test_summary_with_issues():
    result = sanitize_env({"KEY": "value  "})
    summary = result.summary()
    assert "1 issue" in summary
    assert "KEY" in summary
