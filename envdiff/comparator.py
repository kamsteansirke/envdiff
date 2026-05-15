"""Compare two parsed .env dicts and surface missing or mismatched keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Set


@dataclass
class EnvDiff:
    """Result of comparing a base env against a target env."""

    base_name: str
    target_name: str
    missing_in_target: Set[str] = field(default_factory=set)
    missing_in_base: Set[str] = field(default_factory=set)
    mismatched: Dict[str, tuple] = field(default_factory=dict)  # key -> (base_val, target_val)

    def has_differences(self) -> bool:
        return bool(self.missing_in_target or self.missing_in_base or self.mismatched)

    def summary(self) -> str:
        parts = []
        if self.missing_in_target:
            parts.append(f"{len(self.missing_in_target)} missing in {self.target_name}")
        if self.missing_in_base:
            parts.append(f"{len(self.missing_in_base)} extra in {self.target_name}")
        if self.mismatched:
            parts.append(f"{len(self.mismatched)} mismatched")
        if not parts:
            return f"{self.base_name} vs {self.target_name}: identical"
        return f"{self.base_name} vs {self.target_name}: " + ", ".join(parts)

    def stats(self) -> Dict[str, int]:
        return {
            "missing_in_target": len(self.missing_in_target),
            "missing_in_base": len(self.missing_in_base),
            "mismatched": len(self.mismatched),
        }


def has_differences(diff: EnvDiff) -> bool:
    return diff.has_differences()


def summary(diff: EnvDiff) -> str:
    return diff.summary()


def stats(diff: EnvDiff) -> Dict[str, int]:
    return diff.stats()


def compare_envs(
    base: Dict[str, str],
    target: Dict[str, str],
    base_name: str = "base",
    target_name: str = "target",
    ignore_values: bool = False,
) -> EnvDiff:
    """Compare *base* against *target* and return an :class:`EnvDiff`."""
    base_keys = set(base)
    target_keys = set(target)

    missing_in_target = base_keys - target_keys
    missing_in_base = target_keys - base_keys

    mismatched: Dict[str, tuple] = {}
    if not ignore_values:
        for key in base_keys & target_keys:
            if base[key] != target[key]:
                mismatched[key] = (base[key], target[key])

    return EnvDiff(
        base_name=base_name,
        target_name=target_name,
        missing_in_target=missing_in_target,
        missing_in_base=missing_in_base,
        mismatched=mismatched,
    )
