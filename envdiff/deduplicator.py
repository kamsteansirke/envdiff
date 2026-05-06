"""Detect duplicate keys within a single .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class DuplicateEntry:
    key: str
    lines: List[int]  # 1-based line numbers where the key appears

    def __str__(self) -> str:
        lnums = ", ".join(str(n) for n in self.lines)
        return f"{self.key} (lines {lnums})"


@dataclass
class DeduplicateResult:
    path: Path
    duplicates: List[DuplicateEntry] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return len(self.duplicates) > 0

    def summary(self) -> str:
        if not self.has_duplicates:
            return f"{self.path}: no duplicate keys found"
        lines = [f"{self.path}: {len(self.duplicates)} duplicate key(s) found"]
        for entry in self.duplicates:
            lines.append(f"  - {entry}")
        return "\n".join(lines)


def find_duplicates(path: Path) -> DeduplicateResult:
    """Scan *path* for repeated keys and return a DeduplicateResult."""
    seen: Dict[str, List[int]] = {}
    with path.open(encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key = line.split("=", 1)[0].strip()
            # Strip optional 'export ' prefix
            if key.lower().startswith("export "):
                key = key[7:].strip()
            seen.setdefault(key, []).append(lineno)

    duplicates = [
        DuplicateEntry(key=k, lines=v)
        for k, v in seen.items()
        if len(v) > 1
    ]
    duplicates.sort(key=lambda d: d.lines[0])
    return DeduplicateResult(path=path, duplicates=duplicates)
