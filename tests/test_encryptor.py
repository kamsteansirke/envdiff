"""Tests for envdiff.encryptor."""
from __future__ import annotations

import pytest

pytest.importorskip("cryptography", reason="cryptography not installed")

from envdiff.encryptor import (
    EncryptionError,
    EncryptResult,
    decrypt_env,
    encrypt_env,
    generate_key,
)


@pytest.fixture()
def key() -> str:
    return generate_key()


def test_generate_key_returns_string(key):
    assert isinstance(key, str)
    assert len(key) > 0


def test_encrypt_sensitive_key_changes_value(key):
    env = {"DATABASE_PASSWORD": "s3cr3t"}
    result = encrypt_env(env, key)
    assert result.encrypted["DATABASE_PASSWORD"] != "s3cr3t"


def test_encrypt_non_sensitive_key_unchanged(key):
    env = {"PORT": "8080"}
    result = encrypt_env(env, key, sensitive_only=True)
    assert result.encrypted["PORT"] == "8080"
    assert "PORT" in result.skipped


def test_encrypt_all_keys_when_sensitive_only_false(key):
    env = {"PORT": "8080"}
    result = encrypt_env(env, key, sensitive_only=False)
    assert result.encrypted["PORT"] != "8080"
    assert result.skipped == []


def test_encrypted_count(key):
    env = {"API_TOKEN": "abc", "HOST": "localhost"}
    result = encrypt_env(env, key)
    assert result.encrypted_count == 1


def test_summary_string(key):
    env = {"SECRET_KEY": "x", "DEBUG": "true"}
    result = encrypt_env(env, key)
    summary = result.summary()
    assert "encrypted" in summary
    assert "plain text" in summary


def test_decrypt_roundtrip(key):
    env = {"DB_PASSWORD": "hunter2", "PORT": "5432"}
    encrypted = encrypt_env(env, key, sensitive_only=False).encrypted
    decrypted = decrypt_env(encrypted, key)
    assert decrypted == env


def test_decrypt_non_encrypted_value_unchanged(key):
    env = {"PLAIN": "hello"}
    decrypted = decrypt_env(env, key)
    assert decrypted["PLAIN"] == "hello"


def test_invalid_key_raises_encryption_error():
    with pytest.raises(EncryptionError, match="Invalid encryption key"):
        encrypt_env({"FOO": "bar"}, "not-a-valid-key")


def test_original_preserved_in_result(key):
    env = {"API_KEY": "secret"}
    result = encrypt_env(env, key)
    assert result.original == env


def test_mixed_env_encrypt_and_skip(key):
    env = {"API_SECRET": "topsecret", "TIMEOUT": "30", "DB_PASSWORD": "pass"}
    result = encrypt_env(env, key)
    assert "TIMEOUT" in result.skipped
    assert result.encrypted["TIMEOUT"] == "30"
    assert result.encrypted["API_SECRET"] != "topsecret"
    assert result.encrypted["DB_PASSWORD"] != "pass"
