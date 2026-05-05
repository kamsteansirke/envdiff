"""Compare multiple .env files against a single base environment."""

from pathlib import Path
from typing import Dict, List, Optional

from envdiff.comparator import EnvDiff, compare_envs
from envdiff.parser import parse_env_file


def compare_many(
    base_path: Path,
    target_paths: List[Path],
    ignore_values: bool = False,
) -> List[EnvDiff]:
    """Parse base and each target file, returning a list of EnvDiff results.

    Args:
        base_path: Path to the reference .env file.
        target_paths: Paths to .env files to compare against base.
        ignore_values: Forward to compare_envs; only checks key presence when True.

    Returns:
        List of EnvDiff, one per target file.
    """
    base_env: Dict[str, Optional[str]] = parse_env_file(base_path)
    results: List[EnvDiff] = []

    for target_path in target_paths:
        target_env: Dict[str, Optional[str]] = parse_env_file(target_path)
        diff = compare_envs(
            base=base_env,
            target=target_env,
            base_name=base_path.name,
            target_name=target_path.name,
            ignore_values=ignore_values,
        )
        results.append(diff)

    return results


def full_summary(diffs: List[EnvDiff]) -> str:
    """Combine summaries from multiple EnvDiff objects into one string."""
    if not diffs:
        return "No comparisons performed."
    return "\n\n".join(d.summary() for d in diffs)
