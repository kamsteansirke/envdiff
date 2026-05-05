"""Tests for envdiff.auditor and envdiff.cli_audit."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.auditor import AuditViolation, audit_env, audit_many
from envdiff.cli_audit import _run_audit, add_audit_subparser
from envdiff.schema import EnvSchema


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _schema() -> EnvSchema:
    return EnvSchema.from_dict({
        "APP_ENV": {"required": True, "pattern": "^(dev|staging|prod)$"},
        "PORT": {"required": True, "pattern": "^[0-9]+$"},
        "DEBUG": {"required": False},
    })


# ---------------------------------------------------------------------------
# audit_env
# ---------------------------------------------------------------------------

class TestAuditEnv:
    def test_passes_valid_file(self, env_dir: Path) -> None:
        f = _write(env_dir / ".env", "APP_ENV=prod\nPORT=8080\n")
        result = audit_env(str(f), _schema())
        assert result.passed
        assert result.violations == []

    def test_detects_missing_required_key(self, env_dir: Path) -> None:
        f = _write(env_dir / ".env", "APP_ENV=prod\n")
        result = audit_env(str(f), _schema())
        assert not result.passed
        kinds = [v.kind for v in result.violations]
        assert "missing_required" in kinds

    def test_detects_schema_pattern_violation(self, env_dir: Path) -> None:
        f = _write(env_dir / ".env", "APP_ENV=unknown\nPORT=8080\n")
        result = audit_env(str(f), _schema())
        assert not result.passed
        assert any(v.kind == "schema_error" and v.key == "APP_ENV"
                   for v in result.violations)

    def test_undeclared_key_allowed_by_default(self, env_dir: Path) -> None:
        f = _write(env_dir / ".env", "APP_ENV=dev\nPORT=3000\nEXTRA=foo\n")
        result = audit_env(str(f), _schema())
        assert result.passed

    def test_undeclared_key_flagged_in_strict_mode(self, env_dir: Path) -> None:
        f = _write(env_dir / ".env", "APP_ENV=dev\nPORT=3000\nEXTRA=foo\n")
        result = audit_env(str(f), _schema(), allow_undeclared=False)
        assert not result.passed
        assert any(v.kind == "undeclared" and v.key == "EXTRA"
                   for v in result.violations)

    def test_summary_pass(self, env_dir: Path) -> None:
        f = _write(env_dir / ".env", "APP_ENV=dev\nPORT=9000\n")
        result = audit_env(str(f), _schema())
        assert "PASS" in result.summary()

    def test_summary_fail_includes_violations(self, env_dir: Path) -> None:
        f = _write(env_dir / ".env", "APP_ENV=dev\n")
        result = audit_env(str(f), _schema())
        summary = result.summary()
        assert "FAIL" in summary
        assert "PORT" in summary


# ---------------------------------------------------------------------------
# audit_many
# ---------------------------------------------------------------------------

def test_audit_many_returns_one_result_per_file(env_dir: Path) -> None:
    f1 = _write(env_dir / "a.env", "APP_ENV=dev\nPORT=1234\n")
    f2 = _write(env_dir / "b.env", "APP_ENV=prod\n")
    results = audit_many([str(f1), str(f2)], _schema())
    assert len(results) == 2
    assert results[0].passed
    assert not results[1].passed


# ---------------------------------------------------------------------------
# CLI helper
# ---------------------------------------------------------------------------

class FakeArgs:
    def __init__(self, schema: str, envfiles: list, strict: bool = False,
                 output_json: bool = False) -> None:
        self.schema = schema
        self.envfiles = envfiles
        self.strict = strict
        self.output_json = output_json


def test_run_audit_returns_0_on_pass(env_dir: Path) -> None:
    schema_file = env_dir / "schema.json"
    schema_file.write_text(json.dumps({
        "APP_ENV": {"required": True},
    }))
    env_file = _write(env_dir / ".env", "APP_ENV=dev\n")
    args = FakeArgs(str(schema_file), [str(env_file)])
    assert _run_audit(args) == 0


def test_run_audit_returns_1_on_fail(env_dir: Path) -> None:
    schema_file = env_dir / "schema.json"
    schema_file.write_text(json.dumps({
        "APP_ENV": {"required": True},
        "PORT": {"required": True},
    }))
    env_file = _write(env_dir / ".env", "APP_ENV=dev\n")
    args = FakeArgs(str(schema_file), [str(env_file)])
    assert _run_audit(args) == 1


def test_run_audit_returns_2_missing_schema(env_dir: Path) -> None:
    args = FakeArgs(str(env_dir / "no_schema.json"), [])
    assert _run_audit(args) == 2


def test_add_audit_subparser_registers_command() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_audit_subparser(sub)
    parsed = parser.parse_args(["audit", "schema.json", ".env"])
    assert parsed.schema == "schema.json"
    assert parsed.envfiles == [".env"]
    assert not parsed.strict
    assert not parsed.output_json
