"""Tests for envdiff.importer."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envdiff.importer import ImportResult, import_env, ImportError as EnvImportError


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, content: str) -> Path:
    p.write_text(content, encoding="utf-8")
    return p


# --- ImportResult unit tests ---

def test_import_result_key_count():
    r = ImportResult(source="x", entries={"A": "1", "B": "2"})
    assert r.key_count == 2


def test_import_result_is_clean_when_no_skipped():
    r = ImportResult(source="x", entries={"A": "1"})
    assert r.is_clean()


def test_import_result_not_clean_when_skipped():
    r = ImportResult(source="x", entries={}, skipped=["line 1: bad"])
    assert not r.is_clean()


def test_import_result_summary_no_skipped():
    r = ImportResult(source="test.json", entries={"A": "1", "B": "2"})
    assert "2 key(s)" in r.summary()
    assert "skipped" not in r.summary()


def test_import_result_summary_with_skipped():
    r = ImportResult(source="test.sh", entries={"A": "1"}, skipped=["bad line"])
    assert "1 line(s) skipped" in r.summary()


def test_import_result_render_basic():
    r = ImportResult(source="x", entries={"FOO": "bar", "BAZ": "qux"})
    rendered = r.render()
    assert "FOO=bar" in rendered
    assert "BAZ=qux" in rendered


def test_import_result_render_quotes_value_with_space():
    r = ImportResult(source="x", entries={"KEY": "hello world"})
    assert 'KEY="hello world"' in r.render()


def test_import_result_render_quotes_empty_value():
    r = ImportResult(source="x", entries={"EMPTY": ""})
    assert 'EMPTY=""' in r.render()


# --- JSON import ---

def test_import_json_basic(env_dir: Path):
    f = _write(env_dir / "config.json", json.dumps({"DB_HOST": "localhost", "PORT": "5432"}))
    result = import_env(f)
    assert result.entries["DB_HOST"] == "localhost"
    assert result.entries["PORT"] == "5432"
    assert result.is_clean()


def test_import_json_coerces_int_to_str(env_dir: Path):
    f = _write(env_dir / "cfg.json", json.dumps({"TIMEOUT": 30}))
    result = import_env(f)
    assert result.entries["TIMEOUT"] == "30"


def test_import_json_invalid_raises(env_dir: Path):
    f = _write(env_dir / "bad.json", "not json")
    with pytest.raises(EnvImportError, match="Invalid JSON"):
        import_env(f)


def test_import_json_non_object_raises(env_dir: Path):
    f = _write(env_dir / "arr.json", json.dumps(["a", "b"]))
    with pytest.raises(EnvImportError, match="Expected a JSON object"):
        import_env(f)


# --- Shell import ---

def test_import_shell_basic(env_dir: Path):
    f = _write(env_dir / ".env", "FOO=bar\nBAZ=qux\n")
    result = import_env(f, fmt="shell")
    assert result.entries == {"FOO": "bar", "BAZ": "qux"}


def test_import_shell_export_prefix(env_dir: Path):
    f = _write(env_dir / "exports.sh", "export API_KEY=secret\nexport DEBUG=true\n")
    result = import_env(f, fmt="shell")
    assert result.entries["API_KEY"] == "secret"
    assert result.entries["DEBUG"] == "true"


def test_import_shell_strips_quotes(env_dir: Path):
    f = _write(env_dir / ".env", 'GREETING="hello world"\nNAME=\'alice\'\n')
    result = import_env(f, fmt="shell")
    assert result.entries["GREETING"] == "hello world"
    assert result.entries["NAME"] == "alice"


def test_import_shell_skips_comments_and_blanks(env_dir: Path):
    f = _write(env_dir / ".env", "# comment\n\nFOO=1\n")
    result = import_env(f, fmt="shell")
    assert result.key_count == 1
    assert result.is_clean()


def test_import_shell_records_bad_lines(env_dir: Path):
    f = _write(env_dir / ".env", "GOOD=ok\n!!!invalid\n")
    result = import_env(f, fmt="shell")
    assert result.entries == {"GOOD": "ok"}
    assert result.skipped_count == 1
