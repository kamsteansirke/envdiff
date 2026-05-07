"""Pin the current state of an env file so future runs can detect drift."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file


class PinError(Exception):
    """Raised when a pin file cannot be read or is malformed."""


@dataclass
class PinEntry:
    key: str
    value_hash: str  # sha256 hex of the value, or "" if values not pinned
    present: bool = True

    def to_dict(self) -> dict:
        return {"key": self.key, "value_hash": self.value_hash, "present": self.present}

    @classmethod
    def from_dict(cls, d: dict) -> "PinEntry":
        return cls(key=d["key"], value_hash=d.get("value_hash", ""), present=d.get("present", True))


@dataclass
class PinResult:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return not (self.added or self.removed or self.changed)

    def summary(self) -> str:
        if self.is_clean:
            return "No drift detected."
        parts: List[str] = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        if self.changed:
            parts.append(f"{len(self.changed)} changed")
        return "Drift detected: " + ", ".join(parts) + "."


def _hash_value(value: str) -> str:
    import hashlib
    return hashlib.sha256(value.encode()).hexdigest()


def create_pin(env_path: Path, pin_values: bool = False) -> Dict[str, PinEntry]:
    """Capture the current env file state as a pin."""
    data = parse_env_file(env_path)
    return {
        k: PinEntry(key=k, value_hash=_hash_value(v) if pin_values else "")
        for k, v in data.items()
    }


def save_pin(entries: Dict[str, PinEntry], pin_path: Path) -> None:
    pin_path.write_text(
        json.dumps({k: e.to_dict() for k, e in entries.items()}, indent=2),
        encoding="utf-8",
    )


def load_pin(pin_path: Path) -> Dict[str, PinEntry]:
    if not pin_path.exists():
        raise PinError(f"Pin file not found: {pin_path}")
    try:
        raw = json.loads(pin_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PinError(f"Malformed pin file: {exc}") from exc
    return {k: PinEntry.from_dict(v) for k, v in raw.items()}


def check_pin(env_path: Path, pin_path: Path, pin_values: bool = False) -> PinResult:
    """Compare the current env file against a saved pin."""
    pinned = load_pin(pin_path)
    current = create_pin(env_path, pin_values=pin_values)

    result = PinResult()
    for key in current:
        if key not in pinned:
            result.added.append(key)
        elif pin_values and current[key].value_hash != pinned[key].value_hash:
            result.changed.append(key)
    for key in pinned:
        if key not in current:
            result.removed.append(key)
    return result
