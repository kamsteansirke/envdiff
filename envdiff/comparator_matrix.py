"""Build an N×N comparison matrix across multiple .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from envdiff.comparator import EnvDiff, compare
from envdiff.parser import parse_env_file


@dataclass
class MatrixCell:
    base: str
    target: str
    diff: EnvDiff

    @property
    def is_clean(self) -> bool:
        return not self.diff.has_differences()


@dataclass
class MatrixResult:
    env_names: List[str]
    _cells: Dict[Tuple[str, str], MatrixCell] = field(default_factory=dict)

    def cell(self, base: str, target: str) -> MatrixCell | None:
        return self._cells.get((base, target))

    def dirty_pairs(self) -> List[Tuple[str, str]]:
        return [
            (b, t)
            for (b, t), cell in self._cells.items()
            if not cell.is_clean
        ]

    def summary(self) -> str:
        total = len(self._cells)
        dirty = len(self.dirty_pairs())
        clean = total - dirty
        return (
            f"{len(self.env_names)} envs | "
            f"{total} pairs | "
            f"{clean} clean | {dirty} differ"
        )


def build_matrix(
    env_paths: Dict[str, str],
    *,
    ignore_values: bool = False,
) -> MatrixResult:
    """Compare every ordered pair (base, target) of env files."""
    names = sorted(env_paths.keys())
    parsed = {name: parse_env_file(env_paths[name]) for name in names}
    cells: Dict[Tuple[str, str], MatrixCell] = {}

    for base in names:
        for target in names:
            if base == target:
                continue
            diff = compare(parsed[base], parsed[target], ignore_values=ignore_values)
            cells[(base, target)] = MatrixCell(base=base, target=target, diff=diff)

    return MatrixResult(env_names=names, _cells=cells)
