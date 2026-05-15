"""Key rotation helper: detect stale/rotated keys between two env snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RotationCandidate:
    key: str
    old_value: str
    new_value: str
    reason: str = "value_changed"

    def __str__(self) -> str:
        return f"{self.key}: {self.reason}"


@dataclass
class RotationResult:
    candidates: List[RotationCandidate] = field(default_factory=list)
    added_keys: List[str] = field(default_factory=list)
    removed_keys: List[str] = field(default_factory=list)

    @property
    def has_rotations(self) -> bool:
        return bool(self.candidates)

    @property
    def total_changes(self) -> int:
        return len(self.candidates) + len(self.added_keys) + len(self.removed_keys)

    def summary(self) -> str:
        parts = []
        if self.candidates:
            parts.append(f"{len(self.candidates)} rotated")
        if self.added_keys:
            parts.append(f"{len(self.added_keys)} added")
        if self.removed_keys:
            parts.append(f"{len(self.removed_keys)} removed")
        return ", ".join(parts) if parts else "no changes detected"


def rotate_env(
    before: Dict[str, str],
    after: Dict[str, str],
    sensitive_only: bool = False,
    sensitive_patterns: Optional[List[str]] = None,
) -> RotationResult:
    """Compare two env dicts and identify rotated (changed) keys."""
    import re

    _default_patterns = [
        r"(?i)(password|passwd|secret|token|key|api_key|auth|credential|cert|private)"
    ]
    patterns = sensitive_patterns if sensitive_patterns is not None else _default_patterns
    compiled = [re.compile(p) for p in patterns]

    def _is_sensitive(k: str) -> bool:
        return any(p.search(k) for p in compiled)

    before_keys = set(before)
    after_keys = set(after)

    added = sorted(after_keys - before_keys)
    removed = sorted(before_keys - after_keys)
    common = before_keys & after_keys

    candidates: List[RotationCandidate] = []
    for key in sorted(common):
        if sensitive_only and not _is_sensitive(key):
            continue
        old_val = before[key]
        new_val = after[key]
        if old_val != new_val:
            reason = "sensitive_rotated" if _is_sensitive(key) else "value_changed"
            candidates.append(RotationCandidate(key=key, old_value=old_val, new_value=new_val, reason=reason))

    return RotationResult(candidates=candidates, added_keys=added, removed_keys=removed)
