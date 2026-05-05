"""Tests for envdiff.merger."""
from pathlib import Path

import pytest

from envdiff.merger import MergeResult, merge_envs, render_template


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def test_merge_collects_all_keys(env_dir: Path) -> None:
    a = _write(env_dir, ".env.a", "FOO=1\nBAR=2\n")
    b = _write(env_dir, ".env.b", "BAR=2\nBAZ=3\n")
    result = merge_envs([a, b])
    assert result.keys == ["FOO", "BAR", "BAZ"]


def test_merge_records_sources(env_dir: Path) -> None:
    a = _write(env_dir, ".env.a", "FOO=1\n")
    b = _write(env_dir, ".env.b", "FOO=1\nBAR=2\n")
    result = merge_envs([a, b])
    assert result.sources["FOO"] == [".env.a", ".env.b"]
    assert result.sources["BAR"] == [".env.b"]


def test_merge_records_values(env_dir: Path) -> None:
    a = _write(env_dir, ".env.a", "FOO=hello\n")
    b = _write(env_dir, ".env.b", "FOO=world\n")
    result = merge_envs([a, b])
    assert result.values["FOO"] == ["hello", "world"]


def test_merge_ignore_values(env_dir: Path) -> None:
    a = _write(env_dir, ".env.a", "FOO=hello\n")
    b = _write(env_dir, ".env.b", "FOO=world\n")
    result = merge_envs([a, b], ignore_values=True)
    assert result.values["FOO"] == []


def test_is_consistent_same_value(env_dir: Path) -> None:
    a = _write(env_dir, ".env.a", "FOO=same\n")
    b = _write(env_dir, ".env.b", "FOO=same\n")
    result = merge_envs([a, b])
    assert result.is_consistent("FOO") is True


def test_is_consistent_different_values(env_dir: Path) -> None:
    a = _write(env_dir, ".env.a", "FOO=one\n")
    b = _write(env_dir, ".env.b", "FOO=two\n")
    result = merge_envs([a, b])
    assert result.is_consistent("FOO") is False


def test_missing_in(env_dir: Path) -> None:
    a = _write(env_dir, ".env.a", "FOO=1\nBAR=2\n")
    b = _write(env_dir, ".env.b", "FOO=1\n")
    result = merge_envs([a, b])
    assert result.missing_in(".env.b") == ["BAR"]
    assert result.missing_in(".env.a") == []


def test_render_template_contains_all_keys(env_dir: Path) -> None:
    a = _write(env_dir, ".env.a", "FOO=1\nBAR=2\n")
    b = _write(env_dir, ".env.b", "BAZ=3\n")
    result = merge_envs([a, b])
    rendered = render_template(result, comment_sources=False)
    assert "FOO=1" in rendered
    assert "BAR=2" in rendered
    assert "BAZ=3" in rendered


def test_render_template_uses_placeholder_for_disagreement(env_dir: Path) -> None:
    a = _write(env_dir, ".env.a", "FOO=one\n")
    b = _write(env_dir, ".env.b", "FOO=two\n")
    result = merge_envs([a, b])
    rendered = render_template(result, placeholder="CHANGEME", comment_sources=False)
    assert "FOO=CHANGEME" in rendered


def test_render_template_includes_source_comments(env_dir: Path) -> None:
    a = _write(env_dir, ".env.a", "FOO=1\n")
    result = merge_envs([a])
    rendered = render_template(result, comment_sources=True)
    assert "# sources: .env.a" in rendered


def test_render_template_no_source_comments(env_dir: Path) -> None:
    a = _write(env_dir, ".env.a", "FOO=1\n")
    result = merge_envs([a])
    rendered = render_template(result, comment_sources=False)
    assert "#" not in rendered


def test_empty_paths_returns_empty_result() -> None:
    result = merge_envs([])
    assert result.keys == []
    assert result.values == {}
    assert result.sources == {}
