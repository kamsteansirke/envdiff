"""digester.py – compute a deterministic digest (fingerprint) for a .env file.

The digest is an SHA-256 hash of the sorted key=value pairs so that key
ordering in the file does not affect the result.  Optionally the digest
can be computed over keys only (ignoring values) for a structure-only
fingerprint.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from envdiff.parser import parse_env_file


@dataclass
class DigestResult:
    """Holds the fingerprint for a single .env file."""

    path: Path
    digest: str          # hex SHA-256
    key_count: int
    keys_only: bool      # True when values were excluded from the hash

    def short(self, length: int = 12) -> str:
        """Return a shortened digest suitable for display."""
        return self.digest[:length]

    def __str__(self) -> str:  # pragma: no cover
        mode = "keys-only" if self.keys_only else "full"
        return f"{self.short()}  {self.path.name}  ({self.key_count} keys, {mode})"


def digest_env(
    path: Path,
    *,
    keys_only: bool = False,
) -> DigestResult:
    """Parse *path* and return a :class:`DigestResult`."""
    env: Dict[str, str] = parse_env_file(path)
    h = hashlib.sha256()
    for key in sorted(env):
        if keys_only:
            h.update(key.encode())
        else:
            h.update(f"{key}={env[key]}".encode())
    return DigestResult(
        path=path,
        digest=h.hexdigest(),
        key_count=len(env),
        keys_only=keys_only,
    )


def digest_many(
    paths: list[Path],
    *,
    keys_only: bool = False,
) -> list[DigestResult]:
    """Return a :class:`DigestResult` for every path, sorted by file name."""
    return [
        digest_env(p, keys_only=keys_only)
        for p in sorted(paths, key=lambda p: p.name)
    ]


def are_identical(
    a: DigestResult,
    b: DigestResult,
) -> bool:
    """Return *True* when both digests match (same mode assumed by caller)."""
    return a.digest == b.digest


def compare_digests(
    results: list[DigestResult],
) -> Optional[str]:
    """Return the common digest if all results agree, else *None*."""
    if not results:
        return None
    digests = {r.digest for r in results}
    return digests.pop() if len(digests) == 1 else None
