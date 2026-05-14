"""Tests for envdiff.extractor."""
from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.extractor import ExtractResult, extract_env


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content)
    return p


def test_extract_all_keys_when_no_filter(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "A=1\nB=2\nC=3\n")
    result = extract_env(f)
    assert set(result.extracted.keys()) == {"A", "B", "C"}
    assert result.skipped == []


def test_extract_explicit_key(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "A=1\nB=2\nC=3\n")
    result = extract_env(f, keys=["A", "C"])
    assert set(result.extracted.keys()) == {"A", "C"}
    assert "B" in result.skipped


def test_extract_by_pattern(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n")
    result = extract_env(f, patterns=[r"^DB_"])
    assert set(result.extracted.keys()) == {"DB_HOST", "DB_PORT"}
    assert "APP_NAME" in result.skipped


def test_extract_invert_flag(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n")
    result = extract_env(f, patterns=[r"^DB_"], invert=True)
    assert set(result.extracted.keys()) == {"APP_NAME"}
    assert "DB_HOST" in result.skipped


def test_extract_key_count(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "X=1\nY=2\n")
    result = extract_env(f, keys=["X"])
    assert result.key_count == 1
    assert result.skipped_count == 1


def test_extract_is_empty_when_nothing_matches(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "A=1\n")
    result = extract_env(f, keys=["NOPE"])
    assert result.is_empty


def test_extract_render_output(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "Z=hello\nA=world\n")
    result = extract_env(f)
    rendered = result.render()
    assert "A=world" in rendered
    assert "Z=hello" in rendered
    # sorted order: A before Z
    assert rendered.index("A=") < rendered.index("Z=")


def test_extract_render_quotes_value_with_space(env_dir: Path) -> None:
    f = _write(env_dir / ".env", 'GREETING="hello world"\n')
    result = extract_env(f)
    rendered = result.render()
    assert 'GREETING="hello world"' in rendered


def test_extract_summary_string(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "A=1\nB=2\n")
    result = extract_env(f, keys=["A"])
    summary = result.summary()
    assert "extracted 1" in summary
    assert "skipped 1" in summary


def test_extract_combines_keys_and_patterns(env_dir: Path) -> None:
    f = _write(env_dir / ".env", "DB_HOST=h\nDB_PORT=p\nAPP_NAME=n\nDEBUG=1\n")
    result = extract_env(f, keys=["DEBUG"], patterns=[r"^DB_"])
    assert set(result.extracted.keys()) == {"DB_HOST", "DB_PORT", "DEBUG"}
    assert "APP_NAME" in result.skipped
