"""Tests for envdiff.formatter."""
import json
import pytest

from envdiff.formatter import (
    FormatOptions,
    OutputFormat,
    format_env,
    format_export,
    format_dotenv_safe,
    render,
    _is_sensitive,
)


SAMPLE = {"DB_HOST": "localhost", "DB_PASSWORD": "s3cr3t", "PORT": "5432"}


# ---------------------------------------------------------------------------
# _is_sensitive
# ---------------------------------------------------------------------------

def test_is_sensitive_password():
    assert _is_sensitive("DB_PASSWORD", ["PASSWORD", "TOKEN"]) is True


def test_is_not_sensitive_host():
    assert _is_sensitive("DB_HOST", ["PASSWORD", "TOKEN"]) is False


# ---------------------------------------------------------------------------
# format_env
# ---------------------------------------------------------------------------

def test_format_env_basic():
    result = format_env({"FOO": "bar", "BAZ": "qux"})
    assert "FOO=bar" in result
    assert "BAZ=qux" in result


def test_format_env_quotes_value_with_space():
    result = format_env({"MSG": "hello world"})
    assert 'MSG="hello world"' in result


def test_format_env_quotes_empty_value():
    result = format_env({"EMPTY": ""})
    assert 'EMPTY=""' in result


def test_format_env_sort_keys():
    opts = FormatOptions(sort_keys=True)
    result = format_env({"Z": "1", "A": "2"}, opts)
    assert result.index("A=") < result.index("Z=")


def test_format_env_redact_sensitive():
    opts = FormatOptions(redact_sensitive=True)
    result = format_env(SAMPLE, opts)
    assert "<REDACTED>" in result
    assert "s3cr3t" not in result
    assert "localhost" in result


# ---------------------------------------------------------------------------
# format_export
# ---------------------------------------------------------------------------

def test_format_export_prefix():
    result = format_export({"FOO": "bar"})
    assert result.startswith("export FOO=bar")


def test_format_export_redact():
    opts = FormatOptions(redact_sensitive=True)
    result = format_export({"API_KEY": "abc123"}, opts)
    assert "<REDACTED>" in result
    assert "abc123" not in result


# ---------------------------------------------------------------------------
# format_dotenv_safe
# ---------------------------------------------------------------------------

def test_format_dotenv_safe_empty_values():
    result = format_dotenv_safe({"FOO": "bar", "BAZ": "qux"})
    for line in result.splitlines():
        assert line.endswith("=")


def test_format_dotenv_safe_sorted():
    opts = FormatOptions(sort_keys=True)
    result = format_dotenv_safe({"Z": "1", "A": "2"}, opts)
    lines = result.splitlines()
    assert lines[0].startswith("A")
    assert lines[1].startswith("Z")


# ---------------------------------------------------------------------------
# render dispatch
# ---------------------------------------------------------------------------

def test_render_env_format():
    opts = FormatOptions(fmt=OutputFormat.ENV)
    assert "FOO=bar" in render({"FOO": "bar"}, opts)


def test_render_export_format():
    opts = FormatOptions(fmt=OutputFormat.EXPORT)
    assert render({"FOO": "bar"}, opts).startswith("export")


def test_render_json_format():
    opts = FormatOptions(fmt=OutputFormat.JSON)
    data = json.loads(render({"FOO": "bar"}, opts))
    assert data["FOO"] == "bar"


def test_render_json_redact():
    opts = FormatOptions(fmt=OutputFormat.JSON, redact_sensitive=True)
    data = json.loads(render({"SECRET_KEY": "abc"}, opts))
    assert data["SECRET_KEY"] == "<REDACTED>"


def test_render_dotenv_safe_format():
    opts = FormatOptions(fmt=OutputFormat.DOTENV_SAFE)
    result = render({"FOO": "bar"}, opts)
    assert "FOO=" in result
    assert "bar" not in result


def test_render_unknown_format_raises():
    opts = FormatOptions()
    opts.fmt = "unknown"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="Unknown format"):
        render({"FOO": "bar"}, opts)
