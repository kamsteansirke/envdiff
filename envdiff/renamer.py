"""Detect and suggest key renames across two env snapshots.

A rename is heuristically detected when a key disappears in the target
and a new key appears whose value is identical (or very similar) to the
removed key's value in the base environment.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class RenameCandidate:
    old_key: str
    new_key: str
    value: str
    confidence: str  # 'exact' | 'fuzzy'

    def __str__(self) -> str:
        tag = f"[{self.confidence}]"
        return f"{self.old_key} -> {self.new_key}  {tag}  (value: {self.value!r})"


@dataclass
class RenameResult:
    candidates: List[RenameCandidate] = field(default_factory=list)
    unmatched_removed: List[str] = field(default_factory=list)
    unmatched_added: List[str] = field(default_factory=list)

    @property
    def has_candidates(self) -> bool:
        return bool(self.candidates)

    def summary(self) -> str:
        lines: List[str] = []
        if self.candidates:
            lines.append(f"Rename candidates ({len(self.candidates)}):")
            for c in self.candidates:
                lines.append(f"  {c}")
        if self.unmatched_removed:
            lines.append(f"Removed (no match): {', '.join(sorted(self.unmatched_removed))}")
        if self.unmatched_added:
            lines.append(f"Added   (no match): {', '.join(sorted(self.unmatched_added))}")
        return "\n".join(lines) if lines else "No rename candidates found."


def _value_map(env: Dict[str, Optional[str]]) -> Dict[Optional[str], List[str]]:
    """Invert env dict: value -> list of keys with that value."""
    result: Dict[Optional[str], List[str]] = {}
    for k, v in env.items():
        result.setdefault(v, []).append(k)
    return result


def detect_renames(
    base: Dict[str, Optional[str]],
    target: Dict[str, Optional[str]],
) -> RenameResult:
    """Compare *base* and *target* env dicts and return rename candidates.

    Keys present in both environments are ignored; only keys that were
    removed (in base but not target) or added (in target but not base)
    are considered.
    """
    removed = {k: v for k, v in base.items() if k not in target}
    added = {k: v for k, v in target.items() if k not in base}

    if not removed or not added:
        return RenameResult(
            unmatched_removed=list(removed),
            unmatched_added=list(added),
        )

    added_by_value = _value_map(added)
    candidates: List[RenameCandidate] = []
    matched_old: set = set()
    matched_new: set = set()

    for old_key, old_val in sorted(removed.items()):
        new_keys = added_by_value.get(old_val, [])
        available = [k for k in new_keys if k not in matched_new]
        if available:
            new_key = available[0]
            candidates.append(RenameCandidate(old_key, new_key, old_val or "", "exact"))
            matched_old.add(old_key)
            matched_new.add(new_key)

    result = RenameResult(
        candidates=candidates,
        unmatched_removed=[k for k in removed if k not in matched_old],
        unmatched_added=[k for k in added if k not in matched_new],
    )
    return result
