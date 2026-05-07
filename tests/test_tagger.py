"""Tests for envdiff.tagger."""
from __future__ import annotations

import pytest

from envdiff.tagger import TagResult, tag_env


RULES = {
    "database": ["DB_", "DATABASE_"],
    "auth": ["AUTH_", "JWT_", "SECRET_"],
    "infra": ["AWS_", "GCP_"],
}

ENV = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "AUTH_TOKEN": "abc",
    "JWT_SECRET": "xyz",
    "AWS_REGION": "us-east-1",
    "APP_NAME": "myapp",
    "PORT": "8080",
}


def test_tagged_keys_present():
    result = tag_env(ENV, RULES)
    assert "DB_HOST" in result.tagged
    assert "AUTH_TOKEN" in result.tagged
    assert "AWS_REGION" in result.tagged


def test_unmatched_keys_absent():
    result = tag_env(ENV, RULES)
    assert "APP_NAME" not in result.tagged
    assert "PORT" not in result.tagged


def test_tags_for_known_key():
    result = tag_env(ENV, RULES)
    assert "database" in result.tags_for("DB_HOST")


def test_tags_for_unknown_key_returns_empty():
    result = tag_env(ENV, RULES)
    assert result.tags_for("UNKNOWN") == frozenset()


def test_keys_with_tag_sorted():
    result = tag_env(ENV, RULES)
    db_keys = result.keys_with_tag("database")
    assert db_keys == sorted(db_keys)
    assert "DB_HOST" in db_keys
    assert "DB_PORT" in db_keys


def test_keys_with_tag_unknown_tag_returns_empty():
    result = tag_env(ENV, RULES)
    assert result.keys_with_tag("nonexistent") == []


def test_all_tags_returns_union():
    result = tag_env(ENV, RULES)
    tags = result.all_tags()
    assert "database" in tags
    assert "auth" in tags
    assert "infra" in tags


def test_summary_format():
    result = tag_env(ENV, RULES)
    s = result.summary()
    assert "key(s)" in s
    assert "tag(s)" in s


def test_empty_env_returns_empty_result():
    result = tag_env({}, RULES)
    assert result.tagged == {}
    assert result.all_tags() == frozenset()


def test_empty_rules_tags_nothing():
    result = tag_env(ENV, {})
    assert result.tagged == {}


def test_multiple_tags_on_single_key():
    # A key that matches two different rule sets
    env = {"AUTH_DB_KEY": "val"}
    rules = {"auth": ["AUTH_"], "mixed": ["AUTH_DB"]}
    result = tag_env(env, rules)
    tags = result.tags_for("AUTH_DB_KEY")
    assert "auth" in tags
    assert "mixed" in tags
