"""Key-value formatter: render env dicts into various string formats."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class OutputFormat(str, Enum):
    ENV = "env"
    EXPORT = "export"
    JSON = "json"
    DOTENV_SAFE = "dotenv-safe"


@dataclass
class FormatOptions:
    fmt: OutputFormat = OutputFormat.ENV
    sort_keys: bool = False
    include_comments: bool = False
    redact_sensitive: bool = False
    sensitive_patterns: List[str] = field(default_factory=lambda: ["PASSWORD", "SECRET", "TOKEN", "KEY", "API"])


_REDACTED = "<REDACTED>"


def _is_sensitive(key: str, patterns: List[str]) -> bool:
    upper = key.upper()
    return any(p in upper for p in patterns)


def _maybe_redact(key: str, value: str, opts: FormatOptions) -> str:
    if opts.redact_sensitive and _is_sensitive(key, opts.sensitive_patterns):
        return _REDACTED
    return value


def _needs_quoting(value: str) -> bool:
    return " " in value or "\t" in value or "#" in value or value == ""


def _quote(value: str) -> str:
    return f'"{value}"'


def format_env(env: Dict[str, str], opts: Optional[FormatOptions] = None) -> str:
    """Render *env* dict as a .env-style string."""
    opts = opts or FormatOptions()
    keys = sorted(env) if opts.sort_keys else list(env)
    lines: List[str] = []
    for key in keys:
        value = _maybe_redact(key, env[key], opts)
        if _needs_quoting(value):
            value = _quote(value)
        lines.append(f"{key}={value}")
    return "\n".join(lines)


def format_export(env: Dict[str, str], opts: Optional[FormatOptions] = None) -> str:
    """Render *env* dict with 'export KEY=VALUE' syntax (shell-sourceable)."""
    opts = opts or FormatOptions()
    keys = sorted(env) if opts.sort_keys else list(env)
    lines: List[str] = []
    for key in keys:
        value = _maybe_redact(key, env[key], opts)
        if _needs_quoting(value):
            value = _quote(value)
        lines.append(f"export {key}={value}")
    return "\n".join(lines)


def format_dotenv_safe(env: Dict[str, str], opts: Optional[FormatOptions] = None) -> str:
    """Render a dotenv-safe template (.env.example) with empty values."""
    opts = opts or FormatOptions()
    keys = sorted(env) if opts.sort_keys else list(env)
    return "\n".join(f"{key}=" for key in keys)


def render(env: Dict[str, str], opts: Optional[FormatOptions] = None) -> str:
    """Dispatch to the appropriate formatter based on *opts.fmt*."""
    opts = opts or FormatOptions()
    if opts.fmt == OutputFormat.ENV:
        return format_env(env, opts)
    if opts.fmt == OutputFormat.EXPORT:
        return format_export(env, opts)
    if opts.fmt == OutputFormat.DOTENV_SAFE:
        return format_dotenv_safe(env, opts)
    if opts.fmt == OutputFormat.JSON:
        import json
        data = {k: _maybe_redact(k, v, opts) for k, v in env.items()}
        if opts.sort_keys:
            data = dict(sorted(data.items()))
        return json.dumps(data, indent=2)
    raise ValueError(f"Unknown format: {opts.fmt}")
