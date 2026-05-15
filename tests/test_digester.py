"""Tests for envdiff.digester."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.digester import (
    DigestResult,
    are_identical,
    compare_digests,
    digest_env,
    digest_many,
)


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# DigestResult helpers
# ---------------------------------------------------------------------------

def test_short_returns_prefix():
    r = DigestResult(path=Path("x.env"), digest="abcdef1234567890", key_count=1, keys_only=False)
    assert r.short(8) == "abcdef12"


def test_short_default_length():
    r = DigestResult(path=Path("x.env"), digest="a" * 64, key_count=0, keys_only=False)
    assert len(r.short()) == 12


# ---------------------------------------------------------------------------
# digest_env
# ---------------------------------------------------------------------------

def test_digest_env_returns_result(env_dir):
    p = _write(env_dir, ".env", "FOO=bar\nBAZ=qux\n")
    r = digest_env(p)
    assert isinstance(r, DigestResult)
    assert r.key_count == 2
    assert len(r.digest) == 64  # SHA-256 hex
    assert not r.keys_only


def test_digest_env_order_independent(env_dir):
    p1 = _write(env_dir, "a.env", "FOO=bar\nBAZ=qux\n")
    p2 = _write(env_dir, "b.env", "BAZ=qux\nFOO=bar\n")
    assert digest_env(p1).digest == digest_env(p2).digest


def test_digest_env_keys_only_ignores_values(env_dir):
    p1 = _write(env_dir, "a.env", "FOO=bar\n")
    p2 = _write(env_dir, "b.env", "FOO=completely_different\n")
    assert digest_env(p1, keys_only=True).digest == digest_env(p2, keys_only=True).digest


def test_digest_env_keys_only_differs_from_full(env_dir):
    p = _write(env_dir, ".env", "FOO=bar\n")
    assert digest_env(p, keys_only=False).digest != digest_env(p, keys_only=True).digest


def test_digest_env_empty_file(env_dir):
    p = _write(env_dir, ".env", "")
    r = digest_env(p)
    assert r.key_count == 0
    assert len(r.digest) == 64


# ---------------------------------------------------------------------------
# digest_many
# ---------------------------------------------------------------------------

def test_digest_many_sorted_by_name(env_dir):
    _write(env_dir, "z.env", "Z=1\n")
    _write(env_dir, "a.env", "A=1\n")
    paths = list(env_dir.glob("*.env"))
    results = digest_many(paths)
    names = [r.path.name for r in results]
    assert names == sorted(names)


def test_digest_many_empty_list():
    assert digest_many([]) == []


# ---------------------------------------------------------------------------
# are_identical / compare_digests
# ---------------------------------------------------------------------------

def test_are_identical_true(env_dir):
    p = _write(env_dir, ".env", "KEY=val\n")
    r1 = digest_env(p)
    r2 = digest_env(p)
    assert are_identical(r1, r2)


def test_are_identical_false(env_dir):
    p1 = _write(env_dir, "a.env", "KEY=val\n")
    p2 = _write(env_dir, "b.env", "KEY=other\n")
    assert not are_identical(digest_env(p1), digest_env(p2))


def test_compare_digests_all_same(env_dir):
    p = _write(env_dir, ".env", "FOO=1\n")
    results = [digest_env(p), digest_env(p)]
    assert compare_digests(results) == results[0].digest


def test_compare_digests_differ(env_dir):
    p1 = _write(env_dir, "a.env", "FOO=1\n")
    p2 = _write(env_dir, "b.env", "FOO=2\n")
    assert compare_digests([digest_env(p1), digest_env(p2)]) is None


def test_compare_digests_empty():
    assert compare_digests([]) is None
