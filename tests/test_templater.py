"""Tests for envdiff.templater and envdiff.cli_template."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envdiff.templater import TemplateEntry, TemplateResult, build_template
from envdiff.cli_template import add_template_subparser, _run_template


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# TemplateEntry
# ---------------------------------------------------------------------------

def test_entry_render_no_comment():
    e = TemplateEntry(key="DB_HOST", example_value="")
    assert e.render() == "DB_HOST="


def test_entry_render_with_comment():
    e = TemplateEntry(key="DB_HOST", comment="Database hostname", example_value="localhost")
    rendered = e.render()
    assert rendered == "# Database hostname\nDB_HOST=localhost"


# ---------------------------------------------------------------------------
# build_template
# ---------------------------------------------------------------------------

def test_build_template_collects_all_keys(env_dir):
    a = _write(env_dir, "a.env", "FOO=1\nBAR=2\n")
    b = _write(env_dir, "b.env", "BAZ=3\nFOO=overridden\n")
    result = build_template([a, b])
    assert set(result.keys) == {"FOO", "BAR", "BAZ"}


def test_build_template_sorts_keys_by_default(env_dir):
    f = _write(env_dir, "x.env", "ZEBRA=1\nAPPLE=2\nMIDDLE=3\n")
    result = build_template([f])
    assert result.keys == ["APPLE", "MIDDLE", "ZEBRA"]


def test_build_template_no_sort_preserves_order(env_dir):
    f = _write(env_dir, "x.env", "ZEBRA=1\nAPPLE=2\nMIDDLE=3\n")
    result = build_template([f], sort_keys=False)
    assert result.keys == ["ZEBRA", "APPLE", "MIDDLE"]


def test_build_template_placeholder_applied(env_dir):
    f = _write(env_dir, "x.env", "KEY=secret\n")
    result = build_template([f], placeholder="CHANGE_ME")
    assert result.entries[0].example_value == "CHANGE_ME"


def test_build_template_comments_attached(env_dir):
    f = _write(env_dir, "x.env", "API_KEY=abc\n")
    result = build_template([f], comments={"API_KEY": "Your API key"})
    assert result.entries[0].comment == "Your API key"


def test_template_result_render(env_dir):
    f = _write(env_dir, "x.env", "A=1\nB=2\n")
    result = build_template([f])
    rendered = result.render()
    assert "A=" in rendered
    assert "B=" in rendered


def test_template_result_write(env_dir):
    f = _write(env_dir, "x.env", "KEY=val\n")
    out = env_dir / ".env.example"
    result = build_template([f])
    result.write(out)
    content = out.read_text()
    assert "KEY=" in content


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _make_args(**kwargs):
    defaults = dict(files=[], output=None, placeholder="", sort_keys=True, func=_run_template)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_template_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_template_subparser(sub)
    ns = parser.parse_args(["template", "some.env"])
    assert ns.func is _run_template


def test_run_template_missing_file_returns_1(env_dir, capsys):
    args = _make_args(files=[str(env_dir / "missing.env")])
    rc = _run_template(args)
    assert rc == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_run_template_stdout(env_dir, capsys):
    f = _write(env_dir, "t.env", "PORT=8080\n")
    args = _make_args(files=[str(f)])
    rc = _run_template(args)
    assert rc == 0
    assert "PORT=" in capsys.readouterr().out


def test_run_template_writes_file(env_dir, capsys):
    f = _write(env_dir, "t.env", "HOST=localhost\n")
    out = env_dir / ".env.example"
    args = _make_args(files=[str(f)], output=str(out))
    rc = _run_template(args)
    assert rc == 0
    assert out.exists()
    assert "HOST=" in out.read_text()
