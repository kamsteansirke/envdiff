"""Schema validation for .env files.

Allows users to declare required keys (and optional type hints / patterns)
so that envdiff can report not just *differences* between files but also
violations of a declared contract.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    import json
except ImportError:  # pragma: no cover
    json = None  # type: ignore


class SchemaError(ValueError):
    """Raised when the schema definition itself is invalid."""


@dataclass
class KeyRule:
    """Validation rule for a single env key."""

    required: bool = True
    pattern: Optional[str] = None  # regex the value must match
    description: Optional[str] = None

    def validate_value(self, value: str) -> Optional[str]:
        """Return an error message or None if the value is valid."""
        if self.pattern and not re.fullmatch(self.pattern, value):
            return f"value {value!r} does not match pattern {self.pattern!r}"
        return None


@dataclass
class EnvSchema:
    """A collection of key rules that describe a valid .env file."""

    rules: Dict[str, KeyRule] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "EnvSchema":
        """Build an EnvSchema from a plain dictionary (e.g. parsed JSON)."""
        rules: Dict[str, KeyRule] = {}
        for key, spec in data.items():
            if not isinstance(spec, dict):
                raise SchemaError(f"Rule for {key!r} must be a mapping, got {type(spec).__name__}")
            rules[key] = KeyRule(
                required=spec.get("required", True),
                pattern=spec.get("pattern"),
                description=spec.get("description"),
            )
        return cls(rules=rules)

    @classmethod
    def from_json_file(cls, path: Path) -> "EnvSchema":
        """Load a schema from a JSON file on disk."""
        raw = Path(path).read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SchemaError(f"Invalid JSON in schema file {path}: {exc}") from exc
        if not isinstance(data, dict):
            raise SchemaError("Schema JSON must be a top-level object")
        return cls.from_dict(data)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self, env: Dict[str, str]) -> List[str]:
        """Validate *env* against this schema.

        Returns a list of human-readable violation strings (empty = valid).
        """
        violations: List[str] = []
        for key, rule in self.rules.items():
            if key not in env:
                if rule.required:
                    violations.append(f"required key {key!r} is missing")
            else:
                msg = rule.validate_value(env[key])
                if msg:
                    violations.append(f"key {key!r}: {msg}")
        return violations
