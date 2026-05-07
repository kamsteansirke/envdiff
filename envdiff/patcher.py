"""Apply a diff or merge result back to a .env file."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PatchResult:
    """Outcome of a patch operation."""

    applied: List[str] = field(default_factory=list)   # keys that were written/updated
    skipped: List[str] = field(default_factory=list)   # keys already matching target
    removed: List[str] = field(default_factory=list)   # keys deleted (dry_run safe)

    @property
    def is_clean(self) -> bool:
        return not self.applied and not self.removed

    def summary(self) -> str:
        parts = []
        if self.applied:
            parts.append(f"{len(self.applied)} applied")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped")
        return ", ".join(parts) if parts else "no changes"


def _set_key(lines: List[str], key: str, value: str) -> bool:
    """Update an existing key in-place. Returns True if found."""
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = f"{key}={value}\n"
            return True
    return False


def patch_env(
    path: Path,
    updates: Dict[str, str],
    *,
    remove_keys: Optional[List[str]] = None,
    add_missing: bool = True,
    dry_run: bool = False,
) -> PatchResult:
    """Patch *path* with *updates*, optionally removing keys.

    Args:
        path: Target .env file.
        updates: Mapping of key -> desired value.
        remove_keys: Keys to delete from the file.
        add_missing: Append keys not already present.
        dry_run: Compute result without writing.
    """
    remove_keys = remove_keys or []
    lines: List[str] = path.read_text(encoding="utf-8").splitlines(keepends=True)

    result = PatchResult()
    remove_set = set(remove_keys)

    # Remove unwanted keys
    remove_pattern = re.compile(
        r"^\s*(" + "|".join(re.escape(k) for k in remove_set) + r")\s*="
    ) if remove_set else None

    kept: List[str] = []
    for line in lines:
        if remove_pattern and remove_pattern.match(line):
            key_match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
            if key_match:
                result.removed.append(key_match.group(1))
        else:
            kept.append(line)
    lines = kept

    # Apply updates
    for key, value in updates.items():
        if _set_key(lines, key, value):
            result.applied.append(key)
        elif add_missing:
            lines.append(f"{key}={value}\n")
            result.applied.append(key)
        else:
            result.skipped.append(key)

    if not dry_run:
        path.write_text("".join(lines), encoding="utf-8")

    return result
