"""Tests for envdiff.cascader."""
from pathlib import Path

import pytest

from envdiff.cascader import CascadeEntry, CascadeResult, cascade_envs


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# CascadeEntry
# ---------------------------------------------------------------------------

def test_entry_str_includes_key_and_source() -> None:
    e = CascadeEntry(key="FOO", value="bar", source=".env")
    assert "FOO" in str(e)
    assert ".env" in str(e)


# ---------------------------------------------------------------------------
# cascade_envs – basic resolution
# ---------------------------------------------------------------------------

def test_single_layer_returns_all_keys(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "A=1\nB=2\n")
    result = cascade_envs([p])
    assert set(result.keys) == {"A", "B"}


def test_later_layer_wins_on_conflict(env_dir: Path) -> None:
    base = _write(env_dir, ".env", "DB_HOST=localhost\n")
    override = _write(env_dir, ".env.prod", "DB_HOST=prod.db\n")
    result = cascade_envs([base, override])
    assert result.value_for("DB_HOST") == "prod.db"


def test_no_conflict_key_stays_from_base(env_dir: Path) -> None:
    base = _write(env_dir, ".env", "ONLY_BASE=yes\n")
    override = _write(env_dir, ".env.prod", "ONLY_PROD=yes\n")
    result = cascade_envs([base, override])
    assert result.value_for("ONLY_BASE") == "yes"
    assert result.value_for("ONLY_PROD") == "yes"


def test_overrides_list_populated(env_dir: Path) -> None:
    base = _write(env_dir, ".env", "X=1\nY=same\n")
    override = _write(env_dir, ".env.prod", "X=2\nY=same\n")
    result = cascade_envs([base, override])
    assert "X" in result.overrides
    assert "Y" not in result.overrides


def test_three_layers_last_wins(env_dir: Path) -> None:
    a = _write(env_dir, "a.env", "K=alpha\n")
    b = _write(env_dir, "b.env", "K=beta\n")
    c = _write(env_dir, "c.env", "K=gamma\n")
    result = cascade_envs([a, b, c])
    assert result.value_for("K") == "gamma"


# ---------------------------------------------------------------------------
# labels
# ---------------------------------------------------------------------------

def test_custom_labels_used_as_source(env_dir: Path) -> None:
    base = _write(env_dir, ".env", "PORT=8080\n")
    prod = _write(env_dir, ".env.prod", "PORT=443\n")
    result = cascade_envs([base, prod], labels=["base", "prod"])
    assert result.entries["PORT"].source == "prod"
    assert result.layers == ["base", "prod"]


def test_labels_length_mismatch_raises(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "A=1\n")
    with pytest.raises(ValueError, match="labels length"):
        cascade_envs([p], labels=["x", "y"])


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_contains_layer_count(env_dir: Path) -> None:
    a = _write(env_dir, "a.env", "A=1\n")
    b = _write(env_dir, "b.env", "B=2\n")
    result = cascade_envs([a, b])
    s = result.summary()
    assert "2" in s  # two layers
    assert "Total keys" in s


def test_empty_layers_produce_empty_result(env_dir: Path) -> None:
    result = cascade_envs([])
    assert result.keys == []
    assert result.overrides == []
