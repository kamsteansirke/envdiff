"""Compare parsed .env dictionaries and surface differences."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class EnvDiff:
    """Result of comparing two .env files."""

    base_name: str
    target_name: str
    missing_in_target: List[str] = field(default_factory=list)
    missing_in_base: List[str] = field(default_factory=list)
    mismatched: Dict[str, Dict[str, Optional[str]]] = field(default_factory=dict)

    @property
    def has_differences(self) -> bool:
        return bool(
            self.missing_in_target or self.missing_in_base or self.mismatched
        )

    def summary(self) -> str:
        lines = [f"Comparing '{self.base_name}' vs '{self.target_name}'"]
        if not self.has_differences:
            lines.append("  No differences found.")
            return "\n".join(lines)
        if self.missing_in_target:
            lines.append(f"  Missing in {self.target_name}:")
            for key in sorted(self.missing_in_target):
                lines.append(f"    - {key}")
        if self.missing_in_base:
            lines.append(f"  Missing in {self.base_name}:")
            for key in sorted(self.missing_in_base):
                lines.append(f"    + {key}")
        if self.mismatched:
            lines.append("  Mismatched values:")
            for key in sorted(self.mismatched):
                base_val = self.mismatched[key]["base"]
                target_val = self.mismatched[key]["target"]
                lines.append(f"    ~ {key}: {base_val!r} -> {target_val!r}")
        return "\n".join(lines)

    def stats(self) -> Dict[str, int]:
        """Return a summary of difference counts by category.

        Returns:
            A dict with keys 'missing_in_target', 'missing_in_base', and
            'mismatched', each mapping to the count of affected keys.
        """
        return {
            "missing_in_target": len(self.missing_in_target),
            "missing_in_base": len(self.missing_in_base),
            "mismatched": len(self.mismatched),
        }


def compare_envs(
    base: Dict[str, Optional[str]],
    target: Dict[str, Optional[str]],
    base_name: str = "base",
    target_name: str = "target",
    ignore_values: bool = False,
) -> EnvDiff:
    """Compare two env dicts and return an EnvDiff result.

    Args:
        base: Parsed env dict treated as the reference.
        target: Parsed env dict to compare against base.
        base_name: Label for the base env (used in output).
        target_name: Label for the target env (used in output).
        ignore_values: When True, only check for key presence, not value equality.

    Returns:
        EnvDiff instance describing all differences.
    """
    base_keys: Set[str] = set(base.keys())
    target_keys: Set[str] = set(target.keys())

    diff = EnvDiff(base_name=base_name, target_name=target_name)
    diff.missing_in_target = sorted(base_keys - target_keys)
    diff.missing_in_base = sorted(target_keys - base_keys)

    if not ignore_values:
        for key in base_keys & target_keys:
            if base[key] != target[key]:
                diff.mismatched[key] = {"base": base[key], "target": target[key]}

    return diff
