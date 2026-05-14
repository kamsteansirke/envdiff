"""Chain multiple comparisons and aggregate results across a base and many targets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.comparator import EnvDiff, compare_envs


@dataclass
class ChainResult:
    """Aggregated result from chaining a base env against multiple targets."""

    base_name: str
    diffs: Dict[str, EnvDiff] = field(default_factory=dict)

    # --- convenience ---------------------------------------------------

    @property
    def target_names(self) -> List[str]:
        return sorted(self.diffs.keys())

    @property
    def any_differences(self) -> bool:
        return any(d.has_differences for d in self.diffs.values())

    def diff_for(self, target: str) -> Optional[EnvDiff]:
        return self.diffs.get(target)

    def summary(self) -> str:
        lines: List[str] = [f"Base: {self.base_name}"]
        for name in self.target_names:
            diff = self.diffs[name]
            status = "OK" if not diff.has_differences else (
                f"{len(diff.missing_in_target)} missing, "
                f"{len(diff.missing_in_base)} extra, "
                f"{len(diff.mismatched)} mismatched"
            )
            lines.append(f"  vs {name}: {status}")
        return "\n".join(lines)


def compare_chain(
    base: Dict[str, str],
    targets: Dict[str, Dict[str, str]],
    *,
    base_name: str = "base",
    ignore_values: bool = False,
) -> ChainResult:
    """Compare *base* against every entry in *targets*.

    Parameters
    ----------
    base:
        Parsed key/value mapping for the base environment file.
    targets:
        Mapping of {label: parsed_env} for each target to compare.
    base_name:
        Human-readable label for the base environment.
    ignore_values:
        When True, value mismatches are not reported (key presence only).

    Returns
    -------
    ChainResult
        Aggregated diffs keyed by target label.
    """
    result = ChainResult(base_name=base_name)
    for label, target_env in targets.items():
        result.diffs[label] = compare_envs(
            base, target_env, ignore_values=ignore_values
        )
    return result
