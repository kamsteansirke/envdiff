"""Rank multiple env files by their diff severity against a base."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.comparator import EnvDiff, compare
from envdiff.parser import parse_env_file


@dataclass
class RankEntry:
    """A single ranked result for one target env file."""

    name: str
    missing_count: int
    extra_count: int
    mismatch_count: int

    @property
    def total_issues(self) -> int:
        return self.missing_count + self.extra_count + self.mismatch_count

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"{self.name}: {self.total_issues} issue(s) "
            f"(missing={self.missing_count}, "
            f"extra={self.extra_count}, "
            f"mismatch={self.mismatch_count})"
        )


@dataclass
class RankResult:
    """Ranked list of env files from most to least problematic."""

    entries: List[RankEntry] = field(default_factory=list)

    @property
    def best(self) -> RankEntry | None:
        """Entry with the fewest issues (last after sorting)."""
        return self.entries[-1] if self.entries else None

    @property
    def worst(self) -> RankEntry | None:
        """Entry with the most issues (first after sorting)."""
        return self.entries[0] if self.entries else None

    def summary(self) -> str:
        if not self.entries:
            return "No targets to rank."
        lines = [f"Ranked {len(self.entries)} target(s):"]
        for i, e in enumerate(self.entries, 1):
            lines.append(f"  {i}. {e}")
        return "\n".join(lines)


def rank_envs(
    base_path: str,
    target_paths: List[str],
    ignore_values: bool = False,
) -> RankResult:
    """Compare each target against *base* and rank by total issue count.

    Parameters
    ----------
    base_path:
        Path to the reference .env file.
    target_paths:
        Paths to the target .env files to compare and rank.
    ignore_values:
        When *True*, value mismatches are not counted.
    """
    base = parse_env_file(base_path)
    entries: List[RankEntry] = []

    for path in target_paths:
        target = parse_env_file(path)
        diff: EnvDiff = compare(base, target, ignore_values=ignore_values)
        entry = RankEntry(
            name=path,
            missing_count=len(diff.missing_in_target),
            extra_count=len(diff.missing_in_base),
            mismatch_count=len(diff.mismatched),
        )
        entries.append(entry)

    entries.sort(key=lambda e: e.total_issues, reverse=True)
    return RankResult(entries=entries)
