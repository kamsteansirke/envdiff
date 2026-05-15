"""masker.py — Mask sensitive values in a parsed env dict.

Provides a simple way to replace sensitive key values with a
configurable mask string, useful for safe display or logging.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Keys whose values are considered sensitive by default
_SENSITIVE_PATTERNS: List[str] = [
    r"password",
    r"passwd",
    r"secret",
    r"token",
    r"api[_-]?key",
    r"private[_-]?key",
    r"auth",
    r"credential",
    r"cert",
    r"passphrase",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _SENSITIVE_PATTERNS]

DEFAULT_MASK = "***"


def is_sensitive(key: str) -> bool:
    """Return True if *key* matches any built-in sensitive pattern."""
    return any(p.search(key) for p in _COMPILED)


@dataclass
class MaskResult:
    """Result of masking an env mapping."""

    original: Dict[str, str]
    masked: Dict[str, str]
    masked_keys: List[str] = field(default_factory=list)

    @property
    def mask_count(self) -> int:
        return len(self.masked_keys)

    def summary(self) -> str:
        if not self.masked_keys:
            return "No sensitive keys detected."
        keys = ", ".join(sorted(self.masked_keys))
        return f"{self.mask_count} key(s) masked: {keys}"


def mask_env(
    env: Dict[str, str],
    mask: str = DEFAULT_MASK,
    extra_patterns: Optional[List[str]] = None,
    sensitive_only: bool = True,
) -> MaskResult:
    """Return a :class:`MaskResult` with sensitive values replaced by *mask*.

    Parameters
    ----------
    env:
        Parsed key/value mapping.
    mask:
        Replacement string for sensitive values.
    extra_patterns:
        Additional regex patterns (case-insensitive) to treat as sensitive.
    sensitive_only:
        When *False*, mask **all** keys regardless of name.
    """
    extra_compiled = [
        re.compile(p, re.IGNORECASE) for p in (extra_patterns or [])
    ]

    def _is_sensitive(key: str) -> bool:
        if not sensitive_only:
            return True
        return is_sensitive(key) or any(p.search(key) for p in extra_compiled)

    masked: Dict[str, str] = {}
    masked_keys: List[str] = []

    for key, value in env.items():
        if _is_sensitive(key):
            masked[key] = mask
            masked_keys.append(key)
        else:
            masked[key] = value

    return MaskResult(original=env, masked=masked, masked_keys=sorted(masked_keys))
