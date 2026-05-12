"""Tests for envdiff.classifier."""
import pytest
from envdiff.classifier import (
    UNCLASSIFIED,
    ClassifyResult,
    classify_env,
    classify_key,
)


# ---------------------------------------------------------------------------
# classify_key
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key,expected", [
    ("DB_HOST",           "database"),
    ("DATABASE_URL",      "database"),
    ("POSTGRES_PASSWORD", "database"),
    ("SECRET_KEY",        "auth"),
    ("API_KEY",           "auth"),
    ("JWT_TOKEN",         "auth"),
    ("APP_HOST",          "network"),
    ("SERVER_PORT",       "network"),
    ("BACKEND_URL",       "network"),
    ("S3_BUCKET",         "storage"),
    ("STORAGE_PATH",      "storage"),
    ("SMTP_HOST",         "email"),
    ("MAIL_FROM",         "email"),
    ("LOG_LEVEL",         "logging"),
    ("SENTRY_DSN",        "logging"),
    ("FEATURE_FLAG_X",    "feature"),
    ("ENABLE_CACHE",      "feature"),
    ("APP_ENV",           "environment"),
    ("NODE_ENV",          "environment"),
    ("SOME_RANDOM_VAR",   UNCLASSIFIED),
    ("WORKERS",           UNCLASSIFIED),
])
def test_classify_key(key, expected):
    assert classify_key(key) == expected


def test_classify_key_case_insensitive():
    assert classify_key("db_host") == "database"
    assert classify_key("smtp_user") == "email"


# ---------------------------------------------------------------------------
# classify_env
# ---------------------------------------------------------------------------

def test_classify_env_empty():
    result = classify_env({})
    assert isinstance(result, ClassifyResult)
    assert result.categories == {}


def test_classify_env_groups_correctly():
    env = {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "SECRET_KEY": "abc",
        "UNKNOWN_VAR": "x",
    }
    result = classify_env(env)
    assert "database" in result.categories
    assert set(result.keys_for("database")) == {"DB_HOST", "DB_PORT"}
    assert result.keys_for("auth") == ["SECRET_KEY"]
    assert result.keys_for(UNCLASSIFIED) == ["UNKNOWN_VAR"]


def test_all_categories_sorted():
    env = {"LOG_LEVEL": "debug", "DB_URL": "pg://", "APP_HOST": "0.0.0.0"}
    result = classify_env(env)
    cats = result.all_categories()
    assert cats == sorted(cats)


def test_category_for_reverse_lookup():
    env = {"REDIS_URL": "redis://localhost"}
    result = classify_env(env)
    assert result.category_for("REDIS_URL") == "database"
    assert result.category_for("NONEXISTENT") is None


def test_summary_non_empty():
    env = {"DB_HOST": "h", "SECRET": "s", "FOO": "bar"}
    result = classify_env(env)
    text = result.summary()
    assert "database" in text
    assert "auth" in text
    assert "key(s)" in text


def test_summary_empty():
    result = ClassifyResult()
    assert result.summary() == "no keys classified"
