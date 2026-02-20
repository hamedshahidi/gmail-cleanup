from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from app.security import TokenEncryptionError, decrypt_refresh_token, encrypt_refresh_token


def test_encrypt_decrypt_roundtrip() -> None:
    key = Fernet.generate_key().decode("utf-8")
    refresh_token = "refresh-token-123"

    encrypted = encrypt_refresh_token(key, refresh_token)

    assert encrypted != refresh_token
    assert decrypt_refresh_token(key, encrypted) == refresh_token


def test_encrypt_invalid_key_raises() -> None:
    with pytest.raises(TokenEncryptionError, match="valid Fernet key"):
        encrypt_refresh_token("not-a-valid-key", "refresh-token-123")
