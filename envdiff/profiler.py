"""Profile an .env file: count keys, detect patterns, and summarise value types."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envdiff.parser import parse_env_file

_URL_RE = re.compile(r'^https?://', re.IGNORECASE)
_INT_RE = re.compile(r'^-?\d+$')
_BOOL_RE = re.compile(r'^(true|false|yes|no|1|0)$', re.IGNORECASE)
_SECRET_RE = re.compile(r'(secret|password|passwd|token|key|api_?key|private)', re.IGNORECASE)


@dataclass
class ProfileResult:
    path: Path
    total_keys: int
    empty_values: List[str] = field(default_factory=list)
    secret_keys: List[str] = field(default_factory=list)
    url_values: List[str] = field(default_factory=list)
    int_values: List[str] = field(default_factory=list)
    bool_values: List[str] = field(default_factory=list)
    other_values: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Profile: {self.path}",
            f"  Total keys   : {self.total_keys}",
            f"  Empty values : {len(self.empty_values)}",
            f"  Secret keys  : {len(self.secret_keys)}",
            f"  URL values   : {len(self.url_values)}",
            f"  Int values   : {len(self.int_values)}",
            f"  Bool values  : {len(self.bool_values)}",
            f"  Other values : {len(self.other_values)}",
        ]
        return "\n".join(lines)


def profile_env(path: Path) -> ProfileResult:
    """Parse *path* and return a :class:`ProfileResult`."""
    env: Dict[str, str] = parse_env_file(path)
    result = ProfileResult(path=path, total_keys=len(env))

    for key, value in env.items():
        if _SECRET_RE.search(key):
            result.secret_keys.append(key)
        if value == "":
            result.empty_values.append(key)
        elif _BOOL_RE.fullmatch(value):
            result.bool_values.append(key)
        elif _INT_RE.fullmatch(value):
            result.int_values.append(key)
        elif _URL_RE.match(value):
            result.url_values.append(key)
        else:
            result.other_values.append(key)

    return result
