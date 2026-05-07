"""Tests for envdiff.duplicator."""
from __future__ import annotations

import os
import pytest

from envdiff.duplicator import find_duplicate_values, ValueCluster, DuplicateValueResult


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(directory, name: str, content: str) -> str:
    p = directory / name
    p.write_text(content)
    return str(p)


def test_no_duplicates_has_duplicates_false(env_dir):
    path = _write(env_dir, ".env", "A=1\nB=2\nC=3\n")
    result = find_duplicate_values(path)
    assert not result.has_duplicates


def test_no_duplicates_summary(env_dir):
    path = _write(env_dir, ".env", "A=1\nB=2\n")
    result = find_duplicate_values(path)
    assert "no duplicate values" in result.summary()


def test_detects_single_duplicate(env_dir):
    path = _write(env_dir, ".env", "A=hello\nB=hello\nC=world\n")
    result = find_duplicate_values(path)
    assert result.has_duplicates
    assert len(result.clusters) == 1
    cluster = result.clusters[0]
    assert cluster.value == "hello"
    assert set(cluster.keys) == {"A", "B"}


def test_detects_multiple_duplicate_groups(env_dir):
    path = _write(env_dir, ".env", "A=x\nB=x\nC=y\nD=y\nE=z\n")
    result = find_duplicate_values(path)
    assert len(result.clusters) == 2


def test_empty_values_ignored_by_default(env_dir):
    path = _write(env_dir, ".env", "A=\nB=\nC=real\n")
    result = find_duplicate_values(path)
    assert not result.has_duplicates


def test_empty_values_included_when_flag_set(env_dir):
    path = _write(env_dir, ".env", "A=\nB=\nC=real\n")
    result = find_duplicate_values(path, ignore_empty=False)
    assert result.has_duplicates
    assert len(result.clusters) == 1
    assert result.clusters[0].value == ""


def test_summary_lists_keys(env_dir):
    path = _write(env_dir, ".env", "FOO=same\nBAR=same\n")
    result = find_duplicate_values(path)
    summary = result.summary()
    assert "FOO" in summary
    assert "BAR" in summary
    assert "same" in summary


def test_value_cluster_str():
    cluster = ValueCluster(value="abc", keys=["Z", "A"])
    text = str(cluster)
    assert "abc" in text
    assert "A" in text
    assert "Z" in text


def test_result_path_stored(env_dir):
    path = _write(env_dir, ".env", "A=1\n")
    result = find_duplicate_values(path)
    assert result.path == path
