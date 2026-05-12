"""Tests for envdiff.grapher."""
from __future__ import annotations

import pytest

from envdiff.grapher import GraphResult, _refs_in, build_graph


# ---------------------------------------------------------------------------
# _refs_in
# ---------------------------------------------------------------------------

def test_refs_in_brace_syntax():
    assert _refs_in("${FOO}") == frozenset({"FOO"})


def test_refs_in_bare_syntax():
    assert _refs_in("$BAR") == frozenset({"BAR"})


def test_refs_in_multiple():
    assert _refs_in("${A}_${B}") == frozenset({"A", "B"})


def test_refs_in_no_refs():
    assert _refs_in("plain-value") == frozenset()


def test_refs_in_mixed_syntax():
    result = _refs_in("${HOST}:$PORT")
    assert result == frozenset({"HOST", "PORT"})


# ---------------------------------------------------------------------------
# build_graph
# ---------------------------------------------------------------------------

def test_empty_env_produces_empty_graph():
    g = build_graph({})
    assert g.edges == {}
    assert g.undefined_refs == frozenset()


def test_no_references_all_roots():
    env = {"A": "1", "B": "2"}
    g = build_graph(env)
    assert g.roots() == ["A", "B"]
    assert g.undefined_refs == frozenset()


def test_single_reference_recorded():
    env = {"HOST": "localhost", "URL": "http://${HOST}/path"}
    g = build_graph(env)
    assert g.edges["URL"] == frozenset({"HOST"})
    assert g.edges["HOST"] == frozenset()


def test_undefined_ref_detected():
    env = {"URL": "http://${MISSING_HOST}"}
    g = build_graph(env)
    assert "MISSING_HOST" in g.undefined_refs


def test_dependents_of():
    env = {"BASE": "x", "A": "${BASE}-a", "B": "${BASE}-b"}
    g = build_graph(env)
    assert g.dependents_of("BASE") == ["A", "B"]


def test_no_cycle_detected():
    env = {"A": "1", "B": "${A}"}
    g = build_graph(env)
    assert not g.has_cycles()


def test_cycle_detected():
    # A -> B -> A
    env = {"A": "${B}", "B": "${A}"}
    g = build_graph(env)
    assert g.has_cycles()


def test_self_reference_is_cycle():
    env = {"A": "${A}"}
    g = build_graph(env)
    assert g.has_cycles()


def test_summary_no_refs():
    g = build_graph({"X": "1", "Y": "2"})
    s = g.summary()
    assert "2 keys" in s
    assert "0 with references" in s


def test_summary_cycle_flag():
    g = build_graph({"A": "${B}", "B": "${A}"})
    assert "CYCLE" in g.summary()
