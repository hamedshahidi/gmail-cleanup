from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


class TokenEncryptionError(ValueError):
    pass


def _build_fernet(token_enc_key: str) -> Fernet:
    if not token_enc_key:
        raise TokenEncryptionError("TOKEN_ENC_KEY is required.")
    try:
        return Fernet(token_enc_key.encode("utf-8"))
    except Exception as exc:  # pragma: no cover
        raise TokenEncryptionError("TOKEN_ENC_KEY must be a valid Fernet key.") from exc


def encrypt_refresh_token(token_enc_key: str, refresh_token: str) -> str:
    fernet = _build_fernet(token_enc_key)
    return fernet.encrypt(refresh_token.encode("utf-8")).decode("utf-8")


def decrypt_refresh_token(token_enc_key: str, encrypted_token: str) -> str:
    fernet = _build_fernet(token_enc_key)
    try:
        return fernet.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise TokenEncryptionError("Encrypted refresh token is invalid.") from exc
