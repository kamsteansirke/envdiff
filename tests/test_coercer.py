"""Tests for envdiff.coercer."""
from __future__ import annotations

import pytest

from envdiff.coercer import (
    CoerceEntry,
    CoerceResult,
    coerce_env,
    infer_type,
)


# ---------------------------------------------------------------------------
# infer_type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value,expected", [
    ("", "empty"),
    ("true", "bool"),
    ("True", "bool"),
    ("yes", "bool"),
    ("false", "bool"),
    ("no", "bool"),
    ("0", "bool"),
    ("1", "bool"),
    ("on", "bool"),
    ("off", "bool"),
    ("42", "int"),
    ("-7", "int"),
    ("3.14", "float"),
    ("-0.5", "float"),
    ("http://example.com", "url"),
    ("https://api.example.com/v1", "url"),
    ("hello", "string"),
    ("some value with spaces", "string"),
])
def test_infer_type(value, expected):
    assert infer_type(value) == expected


# ---------------------------------------------------------------------------
# CoerceEntry
# ---------------------------------------------------------------------------

def test_coerce_entry_str():
    entry = CoerceEntry(key="PORT", value="8080", inferred_type="int")
    result = str(entry)
    assert "PORT" in result
    assert "int" in result


# ---------------------------------------------------------------------------
# CoerceResult
# ---------------------------------------------------------------------------

def _make_result() -> CoerceResult:
    env = {
        "PORT": "8080",
        "DEBUG": "true",
        "RATIO": "0.75",
        "API_URL": "https://api.example.com",
        "NAME": "myapp",
        "EMPTY_KEY": "",
    }
    return coerce_env(env)


def test_coerce_env_returns_all_keys():
    result = _make_result()
    assert len(result.entries) == 6


def test_coerce_env_entries_sorted_by_key():
    result = _make_result()
    keys = [e.key for e in result.entries]
    assert keys == sorted(keys)


def test_by_type_int():
    result = _make_result()
    ints = result.by_type("int")
    assert len(ints) == 1
    assert ints[0].key == "PORT"


def test_by_type_bool():
    result = _make_result()
    bools = result.by_type("bool")
    assert len(bools) == 1
    assert bools[0].key == "DEBUG"


def test_by_type_empty():
    result = _make_result()
    empties = result.by_type("empty")
    assert len(empties) == 1
    assert empties[0].key == "EMPTY_KEY"


def test_type_counts():
    result = _make_result()
    counts = result.type_counts()
    assert counts["int"] == 1
    assert counts["bool"] == 1
    assert counts["float"] == 1
    assert counts["url"] == 1
    assert counts["string"] == 1
    assert counts["empty"] == 1


def test_summary_contains_key_count():
    result = _make_result()
    assert "6 key(s)" in result.summary()


def test_summary_empty_env():
    result = coerce_env({})
    assert result.summary() == "No keys found."
