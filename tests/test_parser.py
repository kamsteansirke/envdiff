"""Tests for envdiff.parser module."""

import pytest
from pathlib import Path

from envdiff.parser import parse_env_file, EnvParseError


@pytest.fixture
def env_file(tmp_path: Path):
    """Factory fixture that writes content to a temp .env file."""
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def test_basic_key_value(env_file):
    path = env_file("DB_HOST=localhost\nDB_PORT=5432\n")
    result = parse_env_file(path)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_double_quoted_value(env_file):
    path = env_file('SECRET="my secret value"\n')
    result = parse_env_file(path)
    assert result["SECRET"] == "my secret value"


def test_single_quoted_value(env_file):
    path = env_file("TOKEN='abc123'\n")
    result = parse_env_file(path)
    assert result["TOKEN"] == "abc123"


def test_empty_value(env_file):
    path = env_file("EMPTY=\n")
    result = parse_env_file(path)
    assert result["EMPTY"] == ""


def test_comment_lines_ignored(env_file):
    path = env_file("# This is a comment\nKEY=value\n")
    result = parse_env_file(path)
    assert "KEY" in result
    assert len(result) == 1


def test_inline_comment_stripped(env_file):
    path = env_file("HOST=localhost # production host\n")
    result = parse_env_file(path)
    assert result["HOST"] == "localhost"


def test_blank_lines_ignored(env_file):
    path = env_file("\n\nKEY=value\n\n")
    result = parse_env_file(path)
    assert result == {"KEY": "value"}


def test_export_prefix(env_file):
    path = env_file("export API_KEY=supersecret\n")
    result = parse_env_file(path)
    assert result["API_KEY"] == "supersecret"


def test_file_not_found():
    with pytest.raises(EnvParseError, match="File not found"):
        parse_env_file("/nonexistent/path/.env")


def test_invalid_syntax_raises(env_file):
    path = env_file("INVALID_LINE_WITHOUT_EQUALS\n")
    with pytest.raises(EnvParseError, match="Invalid syntax"):
        parse_env_file(path)


def test_empty_key_raises(env_file):
    path = env_file("=value\n")
    with pytest.raises(EnvParseError, match="Empty key"):
        parse_env_file(path)


def test_value_with_equals_sign(env_file):
    path = env_file("JDBC_URL=jdbc:postgresql://host/db?sslmode=require\n")
    result = parse_env_file(path)
    assert result["JDBC_URL"] == "jdbc:postgresql://host/db?sslmode=require"


def test_multiple_entries(env_file):
    content = (
        "# App config\n"
        "APP_ENV=production\n"
        "APP_PORT=8080\n"
        "export APP_SECRET='topsecret'\n"
        "DEBUG=  # disabled\n"
    )
    path = env_file(content)
    result = parse_env_file(path)
    assert result["APP_ENV"] == "production"
    assert result["APP_PORT"] == "8080"
    assert result["APP_SECRET"] == "topsecret"
    assert result["DEBUG"] == ""
