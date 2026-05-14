"""splitter.py – Split a single .env file into multiple files grouped by key prefix."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file
from envdiff.grouper import group_env


@dataclass
class SplitResult:
    """Outcome of splitting one .env file into prefix-based shards."""

    source: Path
    shards: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ungrouped: Dict[str, str] = field(default_factory=dict)

    @property
    def shard_names(self) -> List[str]:
        return sorted(self.shards)

    @property
    def total_keys(self) -> int:
        total = sum(len(v) for v in self.shards.values())
        return total + len(self.ungrouped)

    def summary(self) -> str:
        lines = [f"Source : {self.source}"]
        lines.append(f"Shards : {len(self.shards)}")
        for name in self.shard_names:
            lines.append(f"  [{name}] {len(self.shards[name])} key(s)")
        if self.ungrouped:
            lines.append(f"  [ungrouped] {len(self.ungrouped)} key(s)")
        lines.append(f"Total  : {self.total_keys} key(s)")
        return "\n".join(lines)


def split_env(
    source: Path,
    *,
    sep: str = "_",
    min_prefix_len: int = 2,
    include_ungrouped: bool = True,
) -> SplitResult:
    """Parse *source* and partition keys by their prefix (text before first *sep*).

    Keys whose prefix is shorter than *min_prefix_len* characters land in
    ``ungrouped`` unless *include_ungrouped* is False (they are dropped).
    """
    env = parse_env_file(source)
    group_result = group_env(env, sep=sep, min_prefix_len=min_prefix_len)

    shards: Dict[str, Dict[str, str]] = {}
    for name in group_result.group_names():
        keys = group_result.keys_for(name)  # type: ignore[attr-defined]
        shards[name] = {k: env[k] for k in keys if k in env}

    ungrouped: Dict[str, str] = {}
    if include_ungrouped:
        for k in group_result.ungrouped:  # type: ignore[attr-defined]
            ungrouped[k] = env[k]

    return SplitResult(source=source, shards=shards, ungrouped=ungrouped)


def write_shards(
    result: SplitResult,
    output_dir: Path,
    *,
    ungrouped_name: Optional[str] = "common",
) -> List[Path]:
    """Write each shard in *result* to *output_dir* as ``<name>.env``.

    Returns the list of paths written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []

    for name, mapping in result.shards.items():
        path = output_dir / f"{name}.env"
        path.write_text(_render(mapping))
        written.append(path)

    if result.ungrouped and ungrouped_name:
        path = output_dir / f"{ungrouped_name}.env"
        path.write_text(_render(result.ungrouped))
        written.append(path)

    return sorted(written)


def _render(mapping: Dict[str, str]) -> str:
    return "".join(f"{k}={v}\n" for k, v in sorted(mapping.items()))
