"""Tests for envdiff.constrainer."""
import pytest
from envdiff.constrainer import (
    ConstraintViolation,
    ConstraintResult,
    constrain_env,
)


# ---------------------------------------------------------------------------
# ConstraintViolation
# ---------------------------------------------------------------------------

def test_violation_str_includes_key_and_reason():
    v = ConstraintViolation(key="PORT", value="abc", reason="value must be numeric")
    assert "PORT" in str(v)
    assert "value must be numeric" in str(v)


# ---------------------------------------------------------------------------
# ConstraintResult
# ---------------------------------------------------------------------------

def test_result_is_clean_when_no_violations():
    r = ConstraintResult()
    assert r.is_clean() is True


def test_result_not_clean_when_violations():
    r = ConstraintResult(violations=[ConstraintViolation("K", "", "empty")])
    assert r.is_clean() is False


def test_summary_clean():
    assert "satisfied" in ConstraintResult().summary()


def test_summary_lists_violations():
    r = ConstraintResult(violations=[
        ConstraintViolation("A", "", "must not be empty"),
        ConstraintViolation("B", "x", "must be numeric"),
    ])
    s = r.summary()
    assert "2 constraint" in s
    assert "A" in s
    assert "B" in s


# ---------------------------------------------------------------------------
# constrain_env – require_nonempty
# ---------------------------------------------------------------------------

def test_nonempty_passes_when_value_present():
    result = constrain_env({"HOST": "localhost"}, require_nonempty=["HOST"])
    assert result.is_clean()


def test_nonempty_fails_when_blank():
    result = constrain_env({"HOST": ""}, require_nonempty=["HOST"])
    assert not result.is_clean()
    assert result.violations[0].key == "HOST"


def test_nonempty_skips_missing_key():
    result = constrain_env({}, require_nonempty=["HOST"])
    assert result.is_clean()


# ---------------------------------------------------------------------------
# constrain_env – require_numeric
# ---------------------------------------------------------------------------

def test_numeric_passes_integer():
    result = constrain_env({"PORT": "8080"}, require_numeric=["PORT"])
    assert result.is_clean()


def test_numeric_passes_float():
    result = constrain_env({"RATIO": "0.5"}, require_numeric=["RATIO"])
    assert result.is_clean()


def test_numeric_fails_non_numeric():
    result = constrain_env({"PORT": "abc"}, require_numeric=["PORT"])
    assert not result.is_clean()
    assert "numeric" in result.violations[0].reason


def test_numeric_skips_missing_key():
    result = constrain_env({}, require_numeric=["PORT"])
    assert result.is_clean()


# ---------------------------------------------------------------------------
# constrain_env – allowed_values
# ---------------------------------------------------------------------------

def test_allowed_passes_valid_choice():
    result = constrain_env(
        {"ENV": "production"},
        allowed_values={"ENV": {"development", "staging", "production"}},
    )
    assert result.is_clean()


def test_allowed_fails_invalid_choice():
    result = constrain_env(
        {"ENV": "unknown"},
        allowed_values={"ENV": {"development", "staging", "production"}},
    )
    assert not result.is_clean()
    assert "ENV" in result.violations[0].key


def test_allowed_skips_missing_key():
    result = constrain_env(
        {},
        allowed_values={"ENV": {"dev", "prod"}},
    )
    assert result.is_clean()


# ---------------------------------------------------------------------------
# combined constraints
# ---------------------------------------------------------------------------

def test_multiple_violations_accumulated():
    env = {"PORT": "bad", "HOST": "", "ENV": "invalid"}
    result = constrain_env(
        env,
        require_nonempty=["HOST"],
        require_numeric=["PORT"],
        allowed_values={"ENV": {"dev", "prod"}},
    )
    assert len(result.violations) == 3
