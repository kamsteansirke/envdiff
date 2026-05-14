"""Extract a subset of keys from an env file based on patterns or explicit lists."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file


@dataclass
class ExtractResult:
    source: Path
    extracted: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)

    @property
    def key_count(self) -> int:
        return len(self.extracted)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    @property
    def is_empty(self) -> bool:
        return len(self.extracted) == 0

    def summary(self) -> str:
        return (
            f"{self.source.name}: extracted {self.key_count} key(s), "
            f"skipped {self.skipped_count} key(s)"
        )

    def render(self) -> str:
        """Render the extracted keys as .env content."""
        lines = []
        for key, value in sorted(self.extracted.items()):
            if " " in value or value == "":
                lines.append(f'{key}="{value}"')
            else:
                lines.append(f"{key}={value}")
        return "\n".join(lines) + ("\n" if lines else "")


def extract_env(
    path: Path,
    *,
    keys: Optional[List[str]] = None,
    patterns: Optional[List[str]] = None,
    invert: bool = False,
) -> ExtractResult:
    """Extract keys from *path* matching *keys* and/or *patterns*.

    If *invert* is True, keep keys that do NOT match.
    If neither *keys* nor *patterns* is provided, all keys are extracted.
    """
    env = parse_env_file(path)
    result = ExtractResult(source=path)

    compiled = [re.compile(p) for p in (patterns or [])]
    explicit = set(keys or [])

    for key, value in env.items():
        matched = (
            (not explicit and not compiled)
            or key in explicit
            or any(rx.search(key) for rx in compiled)
        )
        if invert:
            matched = not matched
        if matched:
            result.extracted[key] = value
        else:
            result.skipped.append(key)

    return result
