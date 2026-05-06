"""Tests for envdiff.redactor."""
import pytest
from envdiff.redactor import (
    RedactOptions,
    RedactResult,
    is_sensitive,
    redact_env,
    DEFAULT_PLACEHOLDER,
    _compile_patterns,
)


# ---------------------------------------------------------------------------
# is_sensitive
# ---------------------------------------------------------------------------

def test_is_sensitive_password():
    opts = RedactOptions()
    compiled = _compile_patterns(opts)
    assert is_sensitive("DB_PASSWORD", compiled) is True


def test_is_sensitive_token():
    opts = RedactOptions()
    compiled = _compile_patterns(opts)
    assert is_sensitive("GITHUB_TOKEN", compiled) is True


def test_is_sensitive_api_key():
    opts = RedactOptions()
    compiled = _compile_patterns(opts)
    assert is_sensitive("STRIPE_API_KEY", compiled) is True


def test_is_not_sensitive_plain_key():
    opts = RedactOptions()
    compiled = _compile_patterns(opts)
    assert is_sensitive("APP_NAME", compiled) is False


def test_is_not_sensitive_port():
    opts = RedactOptions()
    compiled = _compile_patterns(opts)
    assert is_sensitive("PORT", compiled) is False


# ---------------------------------------------------------------------------
# redact_env — basic behaviour
# ---------------------------------------------------------------------------

def test_redact_replaces_sensitive_value():
    env = {"DB_PASSWORD": "s3cr3t", "APP_NAME": "myapp"}
    result = redact_env(env)
    assert result.redacted["DB_PASSWORD"] == DEFAULT_PLACEHOLDER
    assert result.redacted["APP_NAME"] == "myapp"


def test_redact_records_redacted_keys():
    env = {"SECRET_KEY": "abc", "AUTH_TOKEN": "xyz", "HOST": "localhost"}
    result = redact_env(env)
    assert "SECRET_KEY" in result.redacted_keys
    assert "AUTH_TOKEN" in result.redacted_keys
    assert "HOST" not in result.redacted_keys


def test_redact_original_unchanged():
    env = {"API_KEY": "real-value"}
    result = redact_env(env)
    assert result.original["API_KEY"] == "real-value"


def test_redact_empty_env():
    result = redact_env({})
    assert result.redacted == {}
    assert result.redacted_keys == []
    assert result.redaction_count == 0


# ---------------------------------------------------------------------------
# RedactOptions — custom placeholder and extra patterns
# ---------------------------------------------------------------------------

def test_custom_placeholder():
    opts = RedactOptions(placeholder="<hidden>")
    result = redact_env({"DB_PASSWORD": "pass"}, options=opts)
    assert result.redacted["DB_PASSWORD"] == "<hidden>"


def test_extra_patterns_extend_defaults():
    opts = RedactOptions(extra_patterns=[r"(?i)webhook"])
    result = redact_env({"WEBHOOK_URL": "https://example.com", "PORT": "8080"}, options=opts)
    assert "WEBHOOK_URL" in result.redacted_keys
    assert "PORT" not in result.redacted_keys


def test_empty_patterns_redacts_nothing():
    opts = RedactOptions(patterns=[])
    result = redact_env({"SECRET": "val", "TOKEN": "t"}, options=opts)
    assert result.redacted_keys == []


# ---------------------------------------------------------------------------
# RedactResult helpers
# ---------------------------------------------------------------------------

def test_summary_no_redactions():
    result = redact_env({"HOST": "localhost"})
    assert result.summary() == "No keys redacted."


def test_summary_with_redactions():
    result = redact_env({"DB_PASSWORD": "x", "API_KEY": "y"})
    assert "2 key(s)" in result.summary()
    assert "API_KEY" in result.summary()
    assert "DB_PASSWORD" in result.summary()


def test_redaction_count():
    result = redact_env({"SECRET": "a", "TOKEN": "b", "NAME": "c"})
    assert result.redaction_count == 2
