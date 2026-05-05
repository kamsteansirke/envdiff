"""Watch .env files for changes and report diffs automatically."""

from __future__ import annotations

import time
import os
from pathlib import Path
from typing import Callable, Dict, Optional

from envdiff.parser import parse_env_file
from envdiff.comparator import compare_envs, EnvDiff
from envdiff.reporter import format_diff, ReportOptions


class EnvWatcher:
    """Poll .env files for modifications and invoke a callback on change."""

    def __init__(
        self,
        base: Path,
        targets: list[Path],
        options: Optional[ReportOptions] = None,
        poll_interval: float = 2.0,
        on_change: Optional[Callable[[str, EnvDiff], None]] = None,
    ) -> None:
        self.base = base
        self.targets = targets
        self.options = options or ReportOptions()
        self.poll_interval = poll_interval
        self.on_change = on_change or self._default_on_change
        self._mtimes: Dict[Path, float] = {}

    # ------------------------------------------------------------------
    def _mtime(self, path: Path) -> float:
        try:
            return os.path.getmtime(path)
        except FileNotFoundError:
            return 0.0

    def _snapshot(self) -> Dict[Path, float]:
        paths = [self.base] + self.targets
        return {p: self._mtime(p) for p in paths}

    def _changed_paths(self, new: Dict[Path, float]) -> list[Path]:
        return [p for p, t in new.items() if t != self._mtimes.get(p, -1)]

    # ------------------------------------------------------------------
    def _default_on_change(self, label: str, diff: EnvDiff) -> None:  # pragma: no cover
        print(f"[envdiff] {label}")
        print(format_diff(diff, self.options))

    def _run_once(self) -> None:
        base_env = parse_env_file(self.base)
        for target in self.targets:
            target_env = parse_env_file(target)
            diff = compare_envs(base_env, target_env, base_name=str(self.base), target_name=str(target))
            if diff.has_differences():
                self.on_change(str(target), diff)

    # ------------------------------------------------------------------
    def watch(self, max_iterations: Optional[int] = None) -> None:
        """Start polling loop. Runs until interrupted or *max_iterations* reached."""
        self._mtimes = self._snapshot()
        iteration = 0
        try:
            while True:
                time.sleep(self.poll_interval)
                new = self._snapshot()
                if self._changed_paths(new):
                    self._run_once()
                    self._mtimes = new
                iteration += 1
                if max_iterations is not None and iteration >= max_iterations:
                    break
        except KeyboardInterrupt:  # pragma: no cover
            pass
