"""Tests for envdiff.flattener."""
import pytest
from envdiff.flattener import FlattenEntry, FlattenResult, flatten_env


# ---------------------------------------------------------------------------
# FlattenEntry
# ---------------------------------------------------------------------------

def test_entry_str():
    e = FlattenEntry(key="DB_HOST", value="localhost", prefix="DB", local_key="HOST")
    assert str(e) == "DB.HOST=localhost"


# ---------------------------------------------------------------------------
# flatten_env – auto-detect prefixes
# ---------------------------------------------------------------------------

def test_auto_prefix_splits_on_first_separator():
    env = {"DB_HOST": "localhost", "DB_PORT": "5432", "PORT": "8080"}
    result = flatten_env(env)
    assert "DB" in result.prefixes
    assert result.keys_for("DB") == ["HOST", "PORT"]
    assert "PORT" in result.unprefixed


def test_unprefixed_key_no_separator():
    env = {"SIMPLE": "value"}
    result = flatten_env(env)
    assert result.prefixes == []
    assert result.unprefixed == {"SIMPLE": "value"}


def test_short_prefix_goes_to_unprefixed():
    # prefix 'A' is length 1 which is < min_prefix_length=2
    env = {"A_KEY": "val"}
    result = flatten_env(env, min_prefix_length=2)
    assert result.prefixes == []
    assert "A_KEY" in result.unprefixed


def test_empty_local_key_goes_to_unprefixed():
    # trailing separator produces empty local key
    env = {"DB_": "val"}
    result = flatten_env(env)
    assert "DB_" in result.unprefixed


# ---------------------------------------------------------------------------
# flatten_env – known_prefixes
# ---------------------------------------------------------------------------

def test_known_prefixes_only_matches_listed():
    env = {"DB_HOST": "h", "AWS_KEY": "k", "OTHER_VAL": "v"}
    result = flatten_env(env, known_prefixes=["DB", "AWS"])
    assert set(result.prefixes) == {"DB", "AWS"}
    assert "OTHER_VAL" in result.unprefixed


def test_known_prefixes_respects_min_length():
    env = {"AB_X": "1", "A_X": "2"}
    result = flatten_env(env, known_prefixes=["AB", "A"], min_prefix_length=2)
    assert "AB" in result.prefixes
    # 'A' is length 1 so should NOT match
    assert "A" not in result.prefixes
    assert "A_X" in result.unprefixed


# ---------------------------------------------------------------------------
# FlattenResult helpers
# ---------------------------------------------------------------------------

def test_as_nested_structure():
    env = {"DB_HOST": "localhost", "DB_PORT": "5432", "AWS_REGION": "us-east-1"}
    result = flatten_env(env)
    nested = result.as_nested()
    assert nested["DB"] == {"HOST": "localhost", "PORT": "5432"}
    assert nested["AWS"] == {"REGION": "us-east-1"}


def test_summary_includes_prefix_and_count():
    env = {"DB_HOST": "h", "DB_PORT": "p", "PORT": "80"}
    result = flatten_env(env)
    s = result.summary()
    assert "[DB]" in s
    assert "2 key(s)" in s
    assert "[unprefixed]" in s


def test_summary_empty():
    result = FlattenResult()
    assert result.summary() == "No keys found."


def test_prefixes_sorted():
    env = {"ZZ_A": "1", "AA_B": "2", "MM_C": "3"}
    result = flatten_env(env)
    assert result.prefixes == ["AA", "MM", "ZZ"]


def test_custom_separator():
    env = {"DB.HOST": "h", "DB.PORT": "p"}
    result = flatten_env(env, separator=".")
    assert "DB" in result.prefixes
    assert result.keys_for("DB") == ["HOST", "PORT"]
