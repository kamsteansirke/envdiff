"""Baseline management: save and load a reference snapshot for drift detection."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from envdiff.parser import parse_env_file


class BaselineError(Exception):
    """Raised when baseline operations fail."""


@dataclass
class Baseline:
    """A saved snapshot of an env file used as a reference point."""

    source: str
    captured_at: str
    keys: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "captured_at": self.captured_at,
            "keys": self.keys,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Baseline":
        return cls(
            source=data["source"],
            captured_at=data["captured_at"],
            keys=data.get("keys", {}),
        )


def capture_baseline(env_path: str) -> Baseline:
    """Parse *env_path* and return a Baseline snapshot."""
    keys = parse_env_file(env_path)
    return Baseline(
        source=os.path.abspath(env_path),
        captured_at=datetime.now(timezone.utc).isoformat(),
        keys=keys,
    )


def save_baseline(baseline: Baseline, output_path: str) -> None:
    """Serialise *baseline* to JSON at *output_path*."""
    Path(output_path).write_text(
        json.dumps(baseline.to_dict(), indent=2), encoding="utf-8"
    )


def load_baseline(path: str) -> Baseline:
    """Load a previously saved baseline from *path*."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"Cannot load baseline from {path!r}: {exc}") from exc
    return Baseline.from_dict(data)


def diff_against_baseline(
    baseline: Baseline, current: Dict[str, str]
) -> Dict[str, object]:
    """Return a dict describing drift between *baseline* and *current* keys."""
    added = {k: current[k] for k in current if k not in baseline.keys}
    removed = {k: baseline.keys[k] for k in baseline.keys if k not in current}
    changed = {
        k: {"baseline": baseline.keys[k], "current": current[k]}
        for k in baseline.keys
        if k in current and baseline.keys[k] != current[k]
    }
    return {"added": added, "removed": removed, "changed": changed}
