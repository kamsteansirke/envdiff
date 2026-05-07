"""Encrypt and decrypt sensitive values in .env files using Fernet symmetric encryption."""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore

from envdiff.redactor import _is_sensitive


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


@dataclass
class EncryptResult:
    original: Dict[str, str]
    encrypted: Dict[str, str]  # sensitive keys have encrypted values
    skipped: List[str] = field(default_factory=list)  # non-sensitive keys

    @property
    def encrypted_count(self) -> int:
        return len(self.encrypted) - len(self.skipped)

    def summary(self) -> str:
        n = self.encrypted_count
        return f"{n} key(s) encrypted, {len(self.skipped)} key(s) left in plain text."


def generate_key() -> str:
    """Generate a new Fernet key and return it as a URL-safe base64 string."""
    if Fernet is None:  # pragma: no cover
        raise EncryptionError("cryptography package is not installed.")
    return Fernet.generate_key().decode()


def encrypt_env(
    env: Dict[str, str],
    key: str,
    *,
    sensitive_only: bool = True,
) -> EncryptResult:
    """Return an EncryptResult with sensitive values encrypted.

    Args:
        env: Parsed key/value mapping.
        key: Fernet key string.
        sensitive_only: When True only keys detected as sensitive are encrypted.
    """
    if Fernet is None:  # pragma: no cover
        raise EncryptionError("cryptography package is not installed.")
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        raise EncryptionError(f"Invalid encryption key: {exc}") from exc

    encrypted: Dict[str, str] = {}
    skipped: List[str] = []

    for k, v in env.items():
        if sensitive_only and not _is_sensitive(k):
            encrypted[k] = v
            skipped.append(k)
        else:
            token = f.encrypt(v.encode()).decode()
            encrypted[k] = token

    return EncryptResult(original=dict(env), encrypted=encrypted, skipped=skipped)


def decrypt_env(env: Dict[str, str], key: str) -> Dict[str, str]:
    """Attempt to decrypt all values; non-encrypted values are returned as-is."""
    if Fernet is None:  # pragma: no cover
        raise EncryptionError("cryptography package is not installed.")
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:
        raise EncryptionError(f"Invalid encryption key: {exc}") from exc

    result: Dict[str, str] = {}
    for k, v in env.items():
        try:
            result[k] = f.decrypt(v.encode()).decode()
        except (InvalidToken, Exception):
            result[k] = v  # not encrypted — keep as-is
    return result
