"""Tests for envdiff.typo_detector."""
import pytest
from envdiff.typo_detector import (
    _edit_distance,
    detect_typos,
    TypoCandidate,
    TypoResult,
)


# ---------------------------------------------------------------------------
# _edit_distance
# ---------------------------------------------------------------------------

def test_edit_distance_identical():
    assert _edit_distance("ABC", "ABC") == 0


def test_edit_distance_insertion():
    assert _edit_distance("ABC", "ABCD") == 1


def test_edit_distance_substitution():
    assert _edit_distance("ABC", "AXC") == 1


def test_edit_distance_empty_strings():
    assert _edit_distance("", "") == 0
    assert _edit_distance("", "AB") == 2
    assert _edit_distance("AB", "") == 2


# ---------------------------------------------------------------------------
# TypoCandidate / TypoResult helpers
# ---------------------------------------------------------------------------

def test_typo_candidate_str():
    c = TypoCandidate(key="DB_HOSR", similar_to="DB_HOST", distance=1)
    assert "DB_HOSR" in str(c)
    assert "DB_HOST" in str(c)
    assert "distance=1" in str(c)


def test_typo_result_has_typos_false_when_empty():
    r = TypoResult()
    assert not r.has_typos


def test_typo_result_has_typos_true():
    r = TypoResult(candidates=[TypoCandidate("DB_HOSR", "DB_HOST", 1)])
    assert r.has_typos


def test_typo_result_summary_no_typos():
    assert "No likely typos" in TypoResult().summary()


def test_typo_result_summary_with_typos():
    r = TypoResult(candidates=[TypoCandidate("DB_HOSR", "DB_HOST", 1)])
    summary = r.summary()
    assert "1 likely typo" in summary
    assert "DB_HOSR" in summary


# ---------------------------------------------------------------------------
# detect_typos
# ---------------------------------------------------------------------------

def test_no_typos_in_distinct_keys():
    env = {"DATABASE_URL": "x", "REDIS_HOST": "y", "SECRET_KEY": "z"}
    result = detect_typos(env)
    assert not result.has_typos


def test_detects_single_character_typo():
    env = {"DB_HOST": "localhost", "DB_HOSR": "localhost"}
    result = detect_typos(env)
    assert result.has_typos
    assert any(c.key == "DB_HOSR" and c.similar_to == "DB_HOST" for c in result.candidates)


def test_ignores_short_keys():
    # Keys shorter than min_key_length should be skipped
    env = {"AB": "1", "AC": "2"}
    result = detect_typos(env, min_key_length=4)
    assert not result.has_typos


def test_case_insensitive_comparison():
    env = {"API_KEY": "a", "API_KEy": "b"}
    result = detect_typos(env)
    assert result.has_typos


def test_max_distance_respected():
    # Distance between DB_HOST and DB_HXYZ is 3; should not fire at default max=2
    env = {"DB_HOST": "a", "DB_HXYZ": "b"}
    result = detect_typos(env, max_distance=2)
    assert not result.has_typos


def test_each_key_reported_at_most_once():
    env = {"REDIS_HOST": "a", "REDIS_HOSR": "b", "REDIS_HOSS": "c"}
    result = detect_typos(env)
    reported_keys = [c.key for c in result.candidates]
    assert len(reported_keys) == len(set(reported_keys))


def test_empty_env_returns_no_typos():
    assert not detect_typos({}).has_typos
