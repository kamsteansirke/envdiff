"""Tests for envdiff.scoper."""
from __future__ import annotations

import pytest

from envdiff.scoper import ScopeEntry, ScopeResult, _detect_scope, scope_env


# ---------------------------------------------------------------------------
# _detect_scope
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key,expected", [
    ("DEV_DATABASE_URL", "DEV"),
    ("PROD_API_KEY", "PROD"),
    ("STAGING_HOST", "STAGING"),
    ("STAGE_HOST", "STAGE"),
    ("TEST_SECRET", "TEST"),
    ("TESTING_MODE", "TESTING"),
    ("QA_ENDPOINT", "QA"),
    ("LOCAL_PORT", "LOCAL"),
    ("CI_TOKEN", "CI"),
    ("SANDBOX_KEY", "SANDBOX"),
    ("DEVELOPMENT_URL", "DEVELOPMENT"),
    ("PRODUCTION_SECRET", "PRODUCTION"),
])
def test_detect_scope_known_prefixes(key, expected):
    assert _detect_scope(key) == expected


def test_detect_scope_unknown_prefix_returns_none():
    assert _detect_scope("DATABASE_URL") is None
    assert _detect_scope("APP_HOST") is None
    assert _detect_scope("SECRET_KEY") is None


def test_detect_scope_case_insensitive():
    assert _detect_scope("dev_host") == "DEV"
    assert _detect_scope("Prod_Secret") == "PROD"


def test_detect_scope_prefix_without_underscore_not_matched():
    # "DEVHOST" has no underscore separator — should not match
    assert _detect_scope("DEVHOST") is None


# ---------------------------------------------------------------------------
# ScopeResult helpers
# ---------------------------------------------------------------------------

def _make_result(*pairs):
    entries = [ScopeEntry(key=k, scope=s) for k, s in pairs]
    return ScopeResult(entries=entries)


def test_scoped_keys_returns_only_scoped():
    r = _make_result(("DEV_HOST", "DEV"), ("DATABASE_URL", None), ("PROD_KEY", "PROD"))
    assert r.scoped_keys() == ["DEV_HOST", "PROD_KEY"]


def test_global_keys_returns_unscoped():
    r = _make_result(("DEV_HOST", "DEV"), ("DATABASE_URL", None))
    assert r.global_keys() == ["DATABASE_URL"]


def test_by_scope_groups_correctly():
    r = _make_result(
        ("DEV_HOST", "DEV"),
        ("DEV_PORT", "DEV"),
        ("PROD_HOST", "PROD"),
        ("APP_NAME", None),
    )
    grouped = r.by_scope()
    assert grouped["DEV"] == ["DEV_HOST", "DEV_PORT"]
    assert grouped["PROD"] == ["PROD_HOST"]
    assert grouped["global"] == ["APP_NAME"]


def test_summary_format():
    r = _make_result(
        ("DEV_HOST", "DEV"),
        ("PROD_HOST", "PROD"),
        ("APP_NAME", None),
    )
    s = r.summary()
    assert "3 keys total" in s
    assert "2 scoped" in s
    assert "1 global" in s


# ---------------------------------------------------------------------------
# scope_env
# ---------------------------------------------------------------------------

def test_scope_env_empty():
    result = scope_env({})
    assert result.entries == []
    assert result.global_keys() == []
    assert result.scoped_keys() == []


def test_scope_env_all_global():
    result = scope_env({"DATABASE_URL": "postgres://", "PORT": "5432"})
    assert result.scoped_keys() == []
    assert set(result.global_keys()) == {"DATABASE_URL", "PORT"}


def test_scope_env_mixed():
    env = {
        "DEV_DB": "sqlite",
        "PROD_DB": "postgres",
        "APP_NAME": "myapp",
    }
    result = scope_env(env)
    assert set(result.scoped_keys()) == {"DEV_DB", "PROD_DB"}
    assert result.global_keys() == ["APP_NAME"]


def test_scope_entry_str_scoped():
    e = ScopeEntry(key="DEV_HOST", scope="DEV")
    assert str(e) == "DEV_HOST [DEV]"


def test_scope_entry_str_global():
    e = ScopeEntry(key="APP_NAME", scope=None)
    assert str(e) == "APP_NAME [global]"
