"""Snapshot capture and comparison for .env drift detection."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file


@dataclass
class SnapshotEntry:
    key: str
    value: str
    captured_at: float

    def to_dict(self) -> dict:
        return {"key": self.key, "value": self.value, "captured_at": self.captured_at}

    @classmethod
    def from_dict(cls, data: dict) -> "SnapshotEntry":
        return cls(key=data["key"], value=data["value"], captured_at=data["captured_at"])


@dataclass
class EnvSnapshot:
    source: str
    captured_at: float
    entries: Dict[str, SnapshotEntry] = field(default_factory=dict)

    def keys(self) -> List[str]:
        return list(self.entries.keys())

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "captured_at": self.captured_at,
            "entries": {k: e.to_dict() for k, e in self.entries.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EnvSnapshot":
        snap = cls(source=data["source"], captured_at=data["captured_at"])
        snap.entries = {k: SnapshotEntry.from_dict(v) for k, v in data["entries"].items()}
        return snap


def capture_snapshot(env_path: Path, ignore_values: bool = False) -> EnvSnapshot:
    """Parse an env file and return an EnvSnapshot."""
    now = time.time()
    parsed = parse_env_file(env_path)
    snap = EnvSnapshot(source=str(env_path), captured_at=now)
    for key, value in parsed.items():
        snap.entries[key] = SnapshotEntry(
            key=key,
            value="" if ignore_values else value,
            captured_at=now,
        )
    return snap


def save_snapshot(snapshot: EnvSnapshot, path: Path) -> None:
    """Persist a snapshot to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot.to_dict(), indent=2))


def load_snapshot(path: Path) -> EnvSnapshot:
    """Load a snapshot from a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {path}")
    data = json.loads(path.read_text())
    return EnvSnapshot.from_dict(data)


def diff_snapshots(old: EnvSnapshot, new: EnvSnapshot) -> Dict[str, str]:
    """Return a dict of {key: change_type} between two snapshots."""
    changes: Dict[str, str] = {}
    old_keys = set(old.entries)
    new_keys = set(new.entries)
    for key in old_keys - new_keys:
        changes[key] = "removed"
    for key in new_keys - old_keys:
        changes[key] = "added"
    for key in old_keys & new_keys:
        if old.entries[key].value != new.entries[key].value:
            changes[key] = "changed"
    return changes
