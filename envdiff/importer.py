"""Import keys from various formats (JSON, TOML-style, shell exports) into .env format."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class ImportError(ValueError):
    """Raised when an import source cannot be parsed."""


@dataclass
class ImportResult:
    source: str
    entries: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)

    @property
    def key_count(self) -> int:
        return len(self.entries)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    def is_clean(self) -> bool:
        return len(self.skipped) == 0

    def summary(self) -> str:
        parts = [f"{self.key_count} key(s) imported from '{self.source}'"]
        if self.skipped:
            parts.append(f"{self.skipped_count} line(s) skipped")
        return "; ".join(parts)

    def render(self) -> str:
        """Render result as .env file content."""
        lines = []
        for key, value in sorted(self.entries.items()):
            if re.search(r'[\s#"\']', value) or value == "":
                lines.append(f'{key}="{value}"')
            else:
                lines.append(f"{key}={value}")
        return "\n".join(lines) + ("\n" if lines else "")


def _import_json(text: str, source: str) -> ImportResult:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON in '{source}': {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError(f"Expected a JSON object in '{source}', got {type(data).__name__}")
    result = ImportResult(source=source)
    for key, val in data.items():
        if not isinstance(key, str):
            result.skipped.append(repr(key))
            continue
        result.entries[key] = str(val) if not isinstance(val, str) else val
    return result


def _import_shell(text: str, source: str) -> ImportResult:
    """Parse lines like: export KEY=VALUE or KEY=VALUE."""
    result = ImportResult(source=source)
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^export\s+", "", line)
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$', line)
        if not m:
            result.skipped.append(f"line {lineno}: {raw!r}")
            continue
        key, val = m.group(1), m.group(2)
        val = val.strip()
        if (val.startswith('"') and val.endswith('"')) or \
           (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        result.entries[key] = val
    return result


def import_env(path: Path, fmt: Optional[str] = None) -> ImportResult:
    """Import a file into an ImportResult. fmt is 'json' or 'shell' (auto-detected if None)."""
    text = path.read_text(encoding="utf-8")
    source = str(path)
    detected = fmt or ("json" if path.suffix.lower() == ".json" else "shell")
    if detected == "json":
        return _import_json(text, source)
    return _import_shell(text, source)
