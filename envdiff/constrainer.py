"""constrainer.py – enforce value constraints on .env keys.

A constraint is a rule that a key's value must satisfy (e.g. non-empty,
numeric, within an allowed set).  Results are collected into a
``ConstraintResult`` that callers can inspect or render.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Collection, Dict, Iterable, Optional


@dataclass
class ConstraintViolation:
    key: str
    value: str
    reason: str

    def __str__(self) -> str:
        return f"{self.key}={self.value!r}: {self.reason}"


@dataclass
class ConstraintResult:
    violations: list[ConstraintViolation] = field(default_factory=list)

    def is_clean(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.is_clean():
            return "All constraints satisfied."
        lines = [f"{len(self.violations)} constraint violation(s):"]
        for v in self.violations:
            lines.append(f"  {v}")
        return "\n".join(lines)


def _check_nonempty(key: str, value: str) -> Optional[ConstraintViolation]:
    if value.strip() == "":
        return ConstraintViolation(key, value, "value must not be empty")
    return None


def _check_numeric(key: str, value: str) -> Optional[ConstraintViolation]:
    try:
        float(value)
        return None
    except ValueError:
        return ConstraintViolation(key, value, "value must be numeric")


def _check_allowed(key: str, value: str, allowed: Collection[str]) -> Optional[ConstraintViolation]:
    if value not in allowed:
        quoted = ", ".join(repr(a) for a in sorted(allowed))
        return ConstraintViolation(key, value, f"value must be one of {quoted}")
    return None


def constrain_env(
    env: Dict[str, str],
    *,
    require_nonempty: Iterable[str] = (),
    require_numeric: Iterable[str] = (),
    allowed_values: Optional[Dict[str, Collection[str]]] = None,
) -> ConstraintResult:
    """Apply constraints to *env* and return a :class:`ConstraintResult`.

    Parameters
    ----------
    env:
        Mapping of key → value (as returned by :func:`envdiff.parser.parse_env_file`).
    require_nonempty:
        Keys whose values must not be blank.
    require_numeric:
        Keys whose values must be parseable as a number.
    allowed_values:
        Mapping of key → allowed value set.
    """
    violations: list[ConstraintViolation] = []
    allowed_values = allowed_values or {}

    for key in require_nonempty:
        if key in env:
            v = _check_nonempty(key, env[key])
            if v:
                violations.append(v)

    for key in require_numeric:
        if key in env:
            v = _check_numeric(key, env[key])
            if v:
                violations.append(v)

    for key, allowed in allowed_values.items():
        if key in env:
            v = _check_allowed(key, env[key], allowed)
            if v:
                violations.append(v)

    return ConstraintResult(violations=violations)
