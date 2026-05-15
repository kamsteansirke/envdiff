"""Tests for envdiff.masker."""
from __future__ import annotations

import pytest

from envdiff.masker import (
    DEFAULT_MASK,
    MaskResult,
    is_sensitive,
    mask_env,
)


# ---------------------------------------------------------------------------
# is_sensitive
# ---------------------------------------------------------------------------


def test_is_sensitive_password():
    assert is_sensitive("DB_PASSWORD") is True


def test_is_sensitive_token():
    assert is_sensitive("AUTH_TOKEN") is True


def test_is_sensitive_api_key():
    assert is_sensitive("API_KEY") is True


def test_is_sensitive_secret():
    assert is_sensitive("APP_SECRET") is True


def test_is_not_sensitive_plain_key():
    assert is_sensitive("APP_HOST") is False


def test_is_not_sensitive_port():
    assert is_sensitive("PORT") is False


# ---------------------------------------------------------------------------
# mask_env
# ---------------------------------------------------------------------------


def test_mask_replaces_sensitive_value():
    env = {"DB_PASSWORD": "s3cr3t", "APP_HOST": "localhost"}
    result = mask_env(env)
    assert result.masked["DB_PASSWORD"] == DEFAULT_MASK
    assert result.masked["APP_HOST"] == "localhost"


def test_mask_count_correct():
    env = {"DB_PASSWORD": "x", "API_KEY": "y", "HOST": "z"}
    result = mask_env(env)
    assert result.mask_count == 2


def test_masked_keys_sorted():
    env = {"TOKEN": "t", "AUTH": "a", "HOST": "h"}
    result = mask_env(env)
    assert result.masked_keys == sorted(result.masked_keys)


def test_original_unchanged():
    env = {"DB_PASSWORD": "secret"}
    result = mask_env(env)
    assert result.original["DB_PASSWORD"] == "secret"


def test_custom_mask_string():
    env = {"API_KEY": "abc"}
    result = mask_env(env, mask="<hidden>")
    assert result.masked["API_KEY"] == "<hidden>"


def test_extra_patterns_extend_sensitivity():
    env = {"STRIPE_ID": "sk_live_123", "HOST": "example.com"}
    result = mask_env(env, extra_patterns=[r"stripe"])
    assert result.masked["STRIPE_ID"] == DEFAULT_MASK
    assert result.masked["HOST"] == "example.com"


def test_sensitive_only_false_masks_all():
    env = {"HOST": "localhost", "PORT": "5432"}
    result = mask_env(env, sensitive_only=False)
    assert result.mask_count == 2
    assert all(v == DEFAULT_MASK for v in result.masked.values())


def test_empty_env_returns_empty_result():
    result = mask_env({})
    assert result.mask_count == 0
    assert result.masked == {}


def test_summary_no_sensitive():
    result = mask_env({"HOST": "localhost"})
    assert result.summary() == "No sensitive keys detected."


def test_summary_with_sensitive():
    result = mask_env({"DB_PASSWORD": "x", "HOST": "y"})
    assert "1 key(s) masked" in result.summary()
    assert "DB_PASSWORD" in result.summary()
