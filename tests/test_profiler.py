"""Tests for envdiff.profiler."""
from pathlib import Path

import pytest

from envdiff.profiler import profile_env, ProfileResult


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def test_total_keys(env_dir):
    p = _write(env_dir, ".env", "A=1\nB=hello\nC=\n")
    result = profile_env(p)
    assert result.total_keys == 3


def test_empty_value_detected(env_dir):
    p = _write(env_dir, ".env", "EMPTY=\nFULL=yes\n")
    result = profile_env(p)
    assert "EMPTY" in result.empty_values
    assert "FULL" not in result.empty_values


def test_bool_values(env_dir):
    p = _write(env_dir, ".env", "FLAG=true\nOTHER=false\nNUM=42\n")
    result = profile_env(p)
    assert "FLAG" in result.bool_values
    assert "OTHER" in result.bool_values
    assert "NUM" not in result.bool_values


def test_int_values(env_dir):
    p = _write(env_dir, ".env", "PORT=8080\nNEG=-3\nWORD=hello\n")
    result = profile_env(p)
    assert "PORT" in result.int_values
    assert "NEG" in result.int_values
    assert "WORD" not in result.int_values


def test_url_values(env_dir):
    p = _write(env_dir, ".env", "API=https://example.com\nOTHER=plain\n")
    result = profile_env(p)
    assert "API" in result.url_values
    assert "OTHER" not in result.url_values


def test_secret_keys(env_dir):
    p = _write(env_dir, ".env", "SECRET_KEY=abc\nAPI_KEY=xyz\nNAME=bob\n")
    result = profile_env(p)
    assert "SECRET_KEY" in result.secret_keys
    assert "API_KEY" in result.secret_keys
    assert "NAME" not in result.secret_keys


def test_summary_contains_path(env_dir):
    p = _write(env_dir, ".env", "X=1\n")
    result = profile_env(p)
    assert str(p) in result.summary()


def test_summary_contains_counts(env_dir):
    p = _write(env_dir, ".env", "PORT=3000\nSECRET_KEY=abc\nFLAG=true\n")
    result = profile_env(p)
    summary = result.summary()
    assert "Total keys   : 3" in summary
    assert "Secret keys  : 1" in summary
    assert "Bool values  : 1" in summary


def test_empty_file(env_dir):
    p = _write(env_dir, ".env", "")
    result = profile_env(p)
    assert result.total_keys == 0
    assert result.empty_values == []
