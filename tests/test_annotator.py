"""Tests for envdiff.annotator and envdiff.cli_annotate."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.annotator import annotate_env, AnnotatedLine
from envdiff.cli_annotate import _run_annotate
from envdiff.schema import EnvSchema


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# annotate_env
# ---------------------------------------------------------------------------

def test_clean_file_has_no_annotations(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "APP_ENV=production\nDEBUG=false\n")
    result = annotate_env(p, include_lint=False)
    assert result.annotated_keys == []


def test_schema_required_adds_annotation(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "DATABASE_URL=postgres://localhost/db\n")
    schema = EnvSchema.from_dict({"DATABASE_URL": {"required": True}})
    result = annotate_env(p, schema=schema, include_lint=False)
    assert "DATABASE_URL" in result.annotated_keys
    rendered = result.render()
    assert "required" in rendered


def test_schema_pattern_adds_annotation(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "PORT=8080\n")
    schema = EnvSchema.from_dict({"PORT": {"pattern": "^\\d+$"}})
    result = annotate_env(p, schema=schema, include_lint=False)
    rendered = result.render()
    assert "pattern=" in rendered


def test_lint_lowercase_key_annotated(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "lowercase_key=value\n")
    result = annotate_env(p, include_lint=True)
    assert "lowercase_key" in result.annotated_keys
    assert "lint:" in result.render()


def test_render_returns_all_lines(env_dir: Path) -> None:
    content = "KEY1=a\nKEY2=b\n"
    p = _write(env_dir, ".env", content)
    result = annotate_env(p, include_lint=False)
    rendered = result.render()
    assert "KEY1=a" in rendered
    assert "KEY2=b" in rendered


def test_comment_lines_not_annotated(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "# this is a comment\nKEY=val\n")
    result = annotate_env(p, include_lint=False)
    comment_line = result.lines[0]
    assert comment_line.key is None
    assert comment_line.note is None


# ---------------------------------------------------------------------------
# AnnotatedLine.render
# ---------------------------------------------------------------------------

def test_annotated_line_render_no_note() -> None:
    ln = AnnotatedLine(raw="KEY=val")
    assert ln.render() == "KEY=val"


def test_annotated_line_render_with_note() -> None:
    ln = AnnotatedLine(raw="KEY=val", key="KEY", note="required")
    assert ln.render() == "KEY=val  # [required]"


# ---------------------------------------------------------------------------
# _run_annotate CLI helper
# ---------------------------------------------------------------------------

class _Args:
    def __init__(self, env_file, schema_file=None, no_lint=False, only_annotated=False):
        self.env_file = env_file
        self.schema_file = schema_file
        self.no_lint = no_lint
        self.only_annotated = only_annotated


def test_run_annotate_missing_file(env_dir: Path) -> None:
    args = _Args(str(env_dir / "nonexistent.env"))
    assert _run_annotate(args) == 2


def test_run_annotate_exits_zero(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "KEY=value\n")
    args = _Args(str(p))
    assert _run_annotate(args) == 0


def test_run_annotate_with_schema_file(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "SECRET_KEY=abc123\n")
    schema_path = _write(
        env_dir,
        "schema.json",
        json.dumps({"SECRET_KEY": {"required": True}}),
    )
    args = _Args(str(p), schema_file=str(schema_path), no_lint=True)
    assert _run_annotate(args) == 0


def test_run_annotate_missing_schema_file(env_dir: Path) -> None:
    p = _write(env_dir, ".env", "KEY=val\n")
    args = _Args(str(p), schema_file=str(env_dir / "no_schema.json"))
    assert _run_annotate(args) == 2
