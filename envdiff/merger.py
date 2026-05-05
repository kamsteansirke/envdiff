"""Merge multiple .env files into a unified template with all known keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from envdiff.parser import parse_env_file


@dataclass
class MergeResult:
    """Result of merging several env files."""

    # Ordered list of all unique keys found across all files
    keys: List[str] = field(default_factory=list)
    # Map of key -> set of distinct values seen (empty string = key present but blank)
    values: Dict[str, List[str]] = field(default_factory=dict)
    # Map of key -> list of source file names that define it
    sources: Dict[str, List[str]] = field(default_factory=dict)

    def is_consistent(self, key: str) -> bool:
        """Return True when all sources agree on the same value for *key*."""
        return len(set(self.values.get(key, []))) <= 1

    def missing_in(self, name: str) -> List[str]:
        """Return keys that do NOT appear in the file identified by *name*."""
        return [k for k in self.keys if name not in self.sources.get(k, [])]


def merge_envs(
    paths: Sequence[Path],
    ignore_values: bool = False,
) -> MergeResult:
    """Parse *paths* and merge all keys into a :class:`MergeResult`.

    Parameters
    ----------
    paths:
        Ordered collection of .env file paths to merge.
    ignore_values:
        When *True* values are not recorded (useful for key-only analysis).
    """
    result = MergeResult()
    seen_keys: dict[str, int] = {}  # key -> insertion order index

    for path in paths:
        name = path.name
        data = parse_env_file(path)
        for key, value in data.items():
            if key not in seen_keys:
                seen_keys[key] = len(result.keys)
                result.keys.append(key)
                result.values[key] = []
                result.sources[key] = []

            result.sources[key].append(name)
            if not ignore_values:
                result.values[key].append(value)

    return result


def render_template(
    result: MergeResult,
    placeholder: str = "",
    comment_sources: bool = True,
) -> str:
    """Render a template .env string containing every key from *result*.

    Parameters
    ----------
    result:
        A :class:`MergeResult` produced by :func:`merge_envs`.
    placeholder:
        Default value to use for keys that have no agreed-upon value.
    comment_sources:
        When *True*, prepend a comment listing source files for each key.
    """
    lines: List[str] = []
    for key in result.keys:
        if comment_sources:
            sources = ", ".join(result.sources.get(key, []))
            lines.append(f"# sources: {sources}")
        unique_values = list(dict.fromkeys(result.values.get(key, [])))
        value: Optional[str] = unique_values[0] if len(unique_values) == 1 else placeholder
        lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")
