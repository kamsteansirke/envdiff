"""Flatten nested or prefixed env keys into a structured dict representation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FlattenEntry:
    key: str
    value: str
    prefix: str
    local_key: str  # key with prefix stripped

    def __str__(self) -> str:
        return f"{self.prefix}.{self.local_key}={self.value}"


@dataclass
class FlattenResult:
    entries: List[FlattenEntry] = field(default_factory=list)
    unprefixed: Dict[str, str] = field(default_factory=dict)

    @property
    def prefixes(self) -> List[str]:
        """Sorted list of distinct prefixes found."""
        return sorted({e.prefix for e in self.entries})

    def keys_for(self, prefix: str) -> List[str]:
        """Local keys under the given prefix, sorted."""
        return sorted(e.local_key for e in self.entries if e.prefix == prefix)

    def as_nested(self) -> Dict[str, Dict[str, str]]:
        """Return {prefix: {local_key: value}} mapping."""
        result: Dict[str, Dict[str, str]] = {}
        for e in self.entries:
            result.setdefault(e.prefix, {})[e.local_key] = e.value
        return result

    def summary(self) -> str:
        lines = []
        for prefix in self.prefixes:
            keys = self.keys_for(prefix)
            lines.append(f"[{prefix}] {len(keys)} key(s): {', '.join(keys)}")
        if self.unprefixed:
            ukeys = sorted(self.unprefixed)
            lines.append(f"[unprefixed] {len(ukeys)} key(s): {', '.join(ukeys)}")
        return "\n".join(lines) if lines else "No keys found."


def flatten_env(
    env: Dict[str, str],
    separator: str = "_",
    min_prefix_length: int = 2,
    known_prefixes: Optional[List[str]] = None,
) -> FlattenResult:
    """Split env keys by *separator* into (prefix, local_key) pairs.

    If *known_prefixes* is provided only those prefixes are recognised;
    otherwise any key containing *separator* is split on the first occurrence.
    Keys that don't match any prefix go into ``unprefixed``.
    """
    entries: List[FlattenEntry] = []
    unprefixed: Dict[str, str] = {}

    for key, value in env.items():
        matched = False
        if known_prefixes:
            for prefix in known_prefixes:
                sep = prefix + separator
                if key.startswith(sep) and len(prefix) >= min_prefix_length:
                    local = key[len(sep):]
                    entries.append(FlattenEntry(key=key, value=value, prefix=prefix, local_key=local))
                    matched = True
                    break
        else:
            if separator in key:
                idx = key.index(separator)
                prefix = key[:idx]
                local = key[idx + len(separator):]
                if len(prefix) >= min_prefix_length and local:
                    entries.append(FlattenEntry(key=key, value=value, prefix=prefix, local_key=local))
                    matched = True

        if not matched:
            unprefixed[key] = value

    return FlattenResult(entries=entries, unprefixed=unprefixed)
