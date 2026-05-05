"""Tests for envdiff.schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.schema import EnvSchema, KeyRule, SchemaError


# ---------------------------------------------------------------------------
# KeyRule
# ---------------------------------------------------------------------------

class TestKeyRule:
    def test_no_pattern_always_valid(self):
        rule = KeyRule()
        assert rule.validate_value("anything") is None

    def test_pattern_match(self):
        rule = KeyRule(pattern=r"\d+")
        assert rule.validate_value("42") is None

    def test_pattern_no_match(self):
        rule = KeyRule(pattern=r"\d+")
        result = rule.validate_value("abc")
        assert result is not None
        assert "pattern" in result


# ---------------------------------------------------------------------------
# EnvSchema.from_dict
# ---------------------------------------------------------------------------

class TestEnvSchemaFromDict:
    def test_basic(self):
        schema = EnvSchema.from_dict({"DB_URL": {"required": True}})
        assert "DB_URL" in schema.rules
        assert schema.rules["DB_URL"].required is True

    def test_defaults_required_true(self):
        schema = EnvSchema.from_dict({"KEY": {}})
        assert schema.rules["KEY"].required is True

    def test_optional_key(self):
        schema = EnvSchema.from_dict({"KEY": {"required": False}})
        assert schema.rules["KEY"].required is False

    def test_invalid_spec_raises(self):
        with pytest.raises(SchemaError, match="must be a mapping"):
            EnvSchema.from_dict({"KEY": "not-a-dict"})


# ---------------------------------------------------------------------------
# EnvSchema.from_json_file
# ---------------------------------------------------------------------------

class TestEnvSchemaFromJsonFile:
    def test_loads_file(self, tmp_path: Path):
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps({"PORT": {"pattern": r"\d+"}}))
        schema = EnvSchema.from_json_file(schema_file)
        assert "PORT" in schema.rules

    def test_invalid_json_raises(self, tmp_path: Path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json {{{")
        with pytest.raises(SchemaError, match="Invalid JSON"):
            EnvSchema.from_json_file(bad)

    def test_non_object_json_raises(self, tmp_path: Path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps(["list", "not", "object"]))
        with pytest.raises(SchemaError, match="top-level object"):
            EnvSchema.from_json_file(bad)


# ---------------------------------------------------------------------------
# EnvSchema.validate
# ---------------------------------------------------------------------------

class TestEnvSchemaValidate:
    def test_valid_env(self):
        schema = EnvSchema.from_dict({"DB_URL": {}, "PORT": {"pattern": r"\d+"}})
        violations = schema.validate({"DB_URL": "postgres://localhost", "PORT": "5432"})
        assert violations == []

    def test_missing_required_key(self):
        schema = EnvSchema.from_dict({"SECRET": {"required": True}})
        violations = schema.validate({})
        assert len(violations) == 1
        assert "SECRET" in violations[0]

    def test_missing_optional_key_no_violation(self):
        schema = EnvSchema.from_dict({"OPTIONAL": {"required": False}})
        violations = schema.validate({})
        assert violations == []

    def test_pattern_violation(self):
        schema = EnvSchema.from_dict({"PORT": {"pattern": r"\d+"}})
        violations = schema.validate({"PORT": "not-a-number"})
        assert len(violations) == 1
        assert "PORT" in violations[0]

    def test_multiple_violations(self):
        schema = EnvSchema.from_dict({
            "A": {"required": True},
            "B": {"pattern": r"[a-z]+"},
        })
        violations = schema.validate({"B": "123"})
        assert len(violations) == 2
