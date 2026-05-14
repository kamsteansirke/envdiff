"""Detect likely typos in .env keys by finding near-duplicate key names."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence


def _edit_distance(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


@dataclass
class TypoCandidate:
    key: str
    similar_to: str
    distance: int

    def __str__(self) -> str:
        return f"{self.key!r} looks like a typo of {self.similar_to!r} (distance={self.distance})"


@dataclass
class TypoResult:
    candidates: List[TypoCandidate] = field(default_factory=list)

    @property
    def has_typos(self) -> bool:
        return bool(self.candidates)

    def summary(self) -> str:
        if not self.candidates:
            return "No likely typos detected."
        lines = [f"{len(self.candidates)} likely typo(s) detected:"]
        for c in sorted(self.candidates, key=lambda x: x.key):
            lines.append(f"  {c}")
        return "\n".join(lines)


def detect_typos(
    env: Dict[str, str],
    max_distance: int = 2,
    min_key_length: int = 4,
) -> TypoResult:
    """Find keys in *env* that are suspiciously similar to other keys.

    Two keys are considered a typo pair when their edit distance is within
    *max_distance* and both are at least *min_key_length* characters long.
    Each key is reported at most once (as the lexicographically smaller key).
    """
    keys: Sequence[str] = sorted(
        k for k in env if len(k) >= min_key_length
    )
    reported: set[str] = set()
    candidates: List[TypoCandidate] = []

    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            if a in reported or b in reported:
                continue
            dist = _edit_distance(a.upper(), b.upper())
            if 0 < dist <= max_distance:
                candidates.append(TypoCandidate(key=b, similar_to=a, distance=dist))
                reported.add(b)

    return TypoResult(candidates=candidates)
