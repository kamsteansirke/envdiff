"""Redact sensitive values from env data based on key patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_DEFAULT_PATTERNS: List[str] = [
    r"(?i)password",
    r"(?i)secret",
    r"(?i)token",
    r"(?i)api[_\-]?key",
    r"(?i)private[_\-]?key",
    r"(?i)auth",
    r"(?i)credential",
]

DEFAULT_PLACEHOLDER = "***REDACTED***"


@dataclass
class RedactOptions:
    patterns: List[str] = field(default_factory=lambda: list(_DEFAULT_PATTERNS))
    placeholder: str = DEFAULT_PLACEHOLDER
    extra_patterns: List[str] = field(default_factory=list)


@dataclass
class RedactResult:
    original: Dict[str, str]
    redacted: Dict[str, str]
    redacted_keys: List[str]

    @property
    def redaction_count(self) -> int:
        return len(self.redacted_keys)

    def summary(self) -> str:
        if not self.redacted_keys:
            return "No keys redacted."
        keys = ", ".join(sorted(self.redacted_keys))
        return f"Redacted {self.redaction_count} key(s): {keys}"


def _compile_patterns(options: RedactOptions) -> List[re.Pattern]:
    all_patterns = options.patterns + options.extra_patterns
    return [re.compile(p) for p in all_patterns]


def is_sensitive(key: str, compiled: List[re.Pattern]) -> bool:
    """Return True if the key matches any sensitive pattern."""
    return any(p.search(key) for p in compiled)


def redact_env(
    env: Dict[str, str],
    options: Optional[RedactOptions] = None,
) -> RedactResult:
    """Return a RedactResult with sensitive values replaced by the placeholder."""
    if options is None:
        options = RedactOptions()
    compiled = _compile_patterns(options)
    redacted: Dict[str, str] = {}
    redacted_keys: List[str] = []
    for key, value in env.items():
        if is_sensitive(key, compiled):
            redacted[key] = options.placeholder
            redacted_keys.append(key)
        else:
            redacted[key] = value
    return RedactResult(
        original=dict(env),
        redacted=redacted,
        redacted_keys=sorted(redacted_keys),
    )
