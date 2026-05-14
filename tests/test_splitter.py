"""Tests for envdiff.splitter."""

from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.splitter import SplitResult, split_env, write_shards


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# SplitResult unit tests
# ---------------------------------------------------------------------------

def test_split_result_shard_names_sorted():
    r = SplitResult(
        source=Path("x.env"),
        shards={"DB": {"DB_HOST": "localhost"}, "APP": {"APP_NAME": "myapp"}},
    )
    assert r.shard_names == ["APP", "DB"]


def test_split_result_total_keys():
    r = SplitResult(
        source=Path("x.env"),
        shards={"DB": {"DB_HOST": "h", "DB_PORT": "5432"}},
        ungrouped={"PORT": "8080"},
    )
    assert r.total_keys == 3


def test_split_result_summary_contains_source(env_dir: Path):
    src = env_dir / ".env"
    r = SplitResult(source=src, shards={"DB": {"DB_HOST": "h"}}, ungrouped={})
    assert str(src) in r.summary()
    assert "[DB]" in r.summary()


# ---------------------------------------------------------------------------
# split_env integration tests
# ---------------------------------------------------------------------------

def test_split_env_groups_by_prefix(env_dir: Path):
    src = _write(
        env_dir / ".env",
        "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\nAPP_ENV=prod\n",
    )
    result = split_env(src)
    assert "DB" in result.shards
    assert "APP" in result.shards
    assert result.shards["DB"] == {"DB_HOST": "localhost", "DB_PORT": "5432"}
    assert result.shards["APP"] == {"APP_NAME": "myapp", "APP_ENV": "prod"}


def test_split_env_ungrouped_collected(env_dir: Path):
    src = _write(env_dir / ".env", "DB_HOST=localhost\nPORT=8080\n")
    result = split_env(src)
    assert "PORT" in result.ungrouped


def test_split_env_ungrouped_excluded_when_flag_false(env_dir: Path):
    src = _write(env_dir / ".env", "DB_HOST=localhost\nPORT=8080\n")
    result = split_env(src, include_ungrouped=False)
    assert result.ungrouped == {}


def test_split_env_empty_file_produces_empty_result(env_dir: Path):
    src = _write(env_dir / ".env", "")
    result = split_env(src)
    assert result.total_keys == 0
    assert result.shards == {}


# ---------------------------------------------------------------------------
# write_shards integration tests
# ---------------------------------------------------------------------------

def test_write_shards_creates_files(env_dir: Path):
    src = _write(
        env_dir / ".env",
        "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n",
    )
    result = split_env(src)
    out_dir = env_dir / "shards"
    written = write_shards(result, out_dir)
    names = {p.name for p in written}
    assert "DB.env" in names
    assert "APP.env" in names


def test_write_shards_content_is_correct(env_dir: Path):
    src = _write(env_dir / ".env", "DB_HOST=localhost\nDB_PORT=5432\n")
    result = split_env(src)
    out_dir = env_dir / "shards"
    write_shards(result, out_dir)
    content = (out_dir / "DB.env").read_text()
    assert "DB_HOST=localhost" in content
    assert "DB_PORT=5432" in content


def test_write_shards_ungrouped_uses_custom_name(env_dir: Path):
    src = _write(env_dir / ".env", "DB_HOST=localhost\nPORT=8080\n")
    result = split_env(src)
    out_dir = env_dir / "shards"
    written = write_shards(result, out_dir, ungrouped_name="misc")
    names = {p.name for p in written}
    assert "misc.env" in names


def test_write_shards_no_ungrouped_file_when_name_none(env_dir: Path):
    src = _write(env_dir / ".env", "DB_HOST=localhost\nPORT=8080\n")
    result = split_env(src)
    out_dir = env_dir / "shards"
    write_shards(result, out_dir, ungrouped_name=None)
    assert not (out_dir / "common.env").exists()
