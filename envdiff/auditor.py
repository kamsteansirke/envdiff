"""Audit .env files against a baseline for compliance reporting."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file
from envdiff.schema import EnvSchema, SchemaError


@dataclass
class AuditViolation:
    key: str
    kind: str  # 'missing_required', 'schema_error', 'undeclared'
    message: str

    def __str__(self) -> str:
        return f"[{self.kind}] {self.key}: {self.message}"


@dataclass
class AuditResult:
    env_file: str
    violations: List[AuditViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.passed:
            return f"{self.env_file}: PASS"
        lines = [f"{self.env_file}: FAIL ({len(self.violations)} violation(s))"]
        for v in self.violations:
            lines.append(f"  {v}")
        return "\n".join(lines)


def audit_env(
    env_path: str,
    schema: EnvSchema,
    *,
    allow_undeclared: bool = True,
) -> AuditResult:
    """Audit a single .env file against *schema*.

    Args:
        env_path: Path to the .env file to audit.
        schema: The :class:`EnvSchema` defining rules and required keys.
        allow_undeclared: When *False*, keys not present in the schema are
            reported as ``undeclared`` violations.

    Returns:
        An :class:`AuditResult` with all violations found.
    """
    result = AuditResult(env_file=env_path)
    env: Dict[str, str] = parse_env_file(env_path)

    # Check required keys and validate values
    for key, rule in schema.rules.items():
        if rule.required and key not in env:
            result.violations.append(
                AuditViolation(key=key, kind="missing_required",
                               message="required key is absent")
            )
            continue
        if key in env:
            error: Optional[str] = rule.validate(env[key])
            if error:
                result.violations.append(
                    AuditViolation(key=key, kind="schema_error", message=error)
                )

    # Check for undeclared keys
    if not allow_undeclared:
        for key in env:
            if key not in schema.rules:
                result.violations.append(
                    AuditViolation(key=key, kind="undeclared",
                                   message="key not declared in schema")
                )

    return result


def audit_many(
    env_paths: List[str],
    schema: EnvSchema,
    *,
    allow_undeclared: bool = True,
) -> List[AuditResult]:
    """Audit multiple .env files, returning one :class:`AuditResult` each."""
    return [
        audit_env(p, schema, allow_undeclared=allow_undeclared)
        for p in env_paths
    ]
