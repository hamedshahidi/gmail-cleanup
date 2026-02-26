from __future__ import annotations

from datetime import UTC

import pytest
from cryptography.fernet import Fernet
from sqlalchemy.orm import sessionmaker

from app.models import GoogleAccount, User
from app.security import encrypt_refresh_token
from app.services.account_messages_service import (
    AccountMessagesService,
    AccountNotFoundOrNotOwnedError,
    AccountTokenInvalidError,
)
from app.services.gmail_client import GmailClientAuthError


class _StubGmailClient:
    def __init__(self, messages: list[dict]) -> None:
        self._messages = messages
        self.calls: list[int] = []

    def list_messages(self, *, max_results: int) -> list[dict]:
        self.calls.append(max_results)
        return self._messages


class _StubGmailClientFactory:
    def __init__(self, *, client: _StubGmailClient | None = None, error: Exception | None = None) -> None:
        self._client = client
        self._error = error
        self.refresh_tokens: list[str] = []

    def create(self, *, refresh_token: str):
        self.refresh_tokens.append(refresh_token)
        if self._error is not None:
            raise self._error
        assert self._client is not None
        return self._client


def _create_user(db_session_local: sessionmaker, *, email: str) -> User:
    with db_session_local() as db:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def _create_account(
    db_session_local: sessionmaker,
    *,
    user_id: int,
    token_encrypted: str,
) -> GoogleAccount:
    with db_session_local() as db:
        account = GoogleAccount(
            user_id=user_id,
            google_sub=f"sub-{user_id}",
            email=f"user{user_id}@gmail.com",
            token_encrypted=token_encrypted,
            scopes="openid email profile",
            last_used_at=None,
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account


def test_list_messages_raises_404_error_for_missing_account(
    testing_session_local: sessionmaker,
) -> None:
    key = Fernet.generate_key().decode("utf-8")
    factory = _StubGmailClientFactory(client=_StubGmailClient([]))
    with testing_session_local() as db:
        service = AccountMessagesService(
            db=db,
            token_enc_key=key,
            gmail_client_factory=factory,
        )
        with pytest.raises(AccountNotFoundOrNotOwnedError):
            service.list_messages(current_user_id=1, account_id=999)


def test_list_messages_raises_404_error_for_unowned_account(
    testing_session_local: sessionmaker,
) -> None:
    owner = _create_user(testing_session_local, email="owner@localhost")
    caller = _create_user(testing_session_local, email="caller@localhost")
    key = Fernet.generate_key().decode("utf-8")
    token = encrypt_refresh_token(key, "refresh-token")
    account = _create_account(
        testing_session_local,
        user_id=owner.id,
        token_encrypted=token,
    )
    factory = _StubGmailClientFactory(client=_StubGmailClient([]))

    with testing_session_local() as db:
        service = AccountMessagesService(
            db=db,
            token_enc_key=key,
            gmail_client_factory=factory,
        )
        with pytest.raises(AccountNotFoundOrNotOwnedError):
            service.list_messages(current_user_id=caller.id, account_id=account.id)


def test_list_messages_raises_account_token_invalid_for_missing_encrypted_token(
    testing_session_local: sessionmaker,
) -> None:
    user = _create_user(testing_session_local, email="u1@localhost")
    account = _create_account(
        testing_session_local,
        user_id=user.id,
        token_encrypted="",
    )
    key = Fernet.generate_key().decode("utf-8")
    factory = _StubGmailClientFactory(client=_StubGmailClient([]))

    with testing_session_local() as db:
        service = AccountMessagesService(
            db=db,
            token_enc_key=key,
            gmail_client_factory=factory,
        )
        with pytest.raises(AccountTokenInvalidError):
            service.list_messages(current_user_id=user.id, account_id=account.id)


def test_list_messages_raises_account_token_invalid_for_decryption_failure(
    testing_session_local: sessionmaker,
) -> None:
    user = _create_user(testing_session_local, email="u2@localhost")
    account = _create_account(
        testing_session_local,
        user_id=user.id,
        token_encrypted="not-a-valid-encrypted-token",
    )
    key = Fernet.generate_key().decode("utf-8")
    factory = _StubGmailClientFactory(client=_StubGmailClient([]))

    with testing_session_local() as db:
        service = AccountMessagesService(
            db=db,
            token_enc_key=key,
            gmail_client_factory=factory,
        )
        with pytest.raises(AccountTokenInvalidError):
            service.list_messages(current_user_id=user.id, account_id=account.id)


def test_list_messages_raises_account_token_invalid_for_gmail_auth_failure(
    testing_session_local: sessionmaker,
) -> None:
    user = _create_user(testing_session_local, email="u3@localhost")
    key = Fernet.generate_key().decode("utf-8")
    token = encrypt_refresh_token(key, "refresh-token-xyz")
    account = _create_account(
        testing_session_local,
        user_id=user.id,
        token_encrypted=token,
    )
    factory = _StubGmailClientFactory(error=GmailClientAuthError("auth failed"))

    with testing_session_local() as db:
        service = AccountMessagesService(
            db=db,
            token_enc_key=key,
            gmail_client_factory=factory,
        )
        with pytest.raises(AccountTokenInvalidError):
            service.list_messages(current_user_id=user.id, account_id=account.id)


def test_list_messages_maps_payload_and_limits_to_ten(
    testing_session_local: sessionmaker,
) -> None:
    user = _create_user(testing_session_local, email="u4@localhost")
    key = Fernet.generate_key().decode("utf-8")
    token = encrypt_refresh_token(key, "refresh-token-abc")
    account = _create_account(
        testing_session_local,
        user_id=user.id,
        token_encrypted=token,
    )
    raw_messages = [
        {
            "id": "m-1",
            "snippet": "snippet-1",
            "internalDate": "1704067200000",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Subject 1"},
                    {"name": "From", "value": "sender1@example.com"},
                ]
            },
        },
        {
            "id": "m-2",
            "snippet": "snippet-2",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Subject 2"},
                    {"name": "From", "value": "sender2@example.com"},
                    {"name": "Date", "value": "Mon, 01 Jan 2024 10:00:00 +0000"},
                ]
            },
        },
    ]
    client = _StubGmailClient(raw_messages)
    factory = _StubGmailClientFactory(client=client)

    with testing_session_local() as db:
        service = AccountMessagesService(
            db=db,
            token_enc_key=key,
            gmail_client_factory=factory,
        )
        messages = service.list_messages(current_user_id=user.id, account_id=account.id)

    assert client.calls == [10]
    assert factory.refresh_tokens == ["refresh-token-abc"]
    assert len(messages) == 2
    assert messages[0].id == "m-1"
    assert messages[0].subject == "Subject 1"
    assert messages[0].from_ == "sender1@example.com"
    assert messages[0].snippet == "snippet-1"
    assert messages[0].date == messages[0].date.astimezone(UTC)
    assert messages[1].id == "m-2"
    assert messages[1].subject == "Subject 2"
    assert messages[1].from_ == "sender2@example.com"
    assert messages[1].snippet == "snippet-2"
