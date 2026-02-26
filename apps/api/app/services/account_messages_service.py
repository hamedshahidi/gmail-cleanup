from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import GoogleAccount
from ..schemas.messages import AccountMessage
from ..security import TokenEncryptionError, decrypt_refresh_token
from .gmail_client import GmailClient, GmailClientAuthError, GmailClientFactory


class AccountNotFoundOrNotOwnedError(LookupError):
    pass


class AccountTokenInvalidError(ValueError):
    pass


class AccountMessagesService:
    def __init__(
        self,
        *,
        db: Session,
        token_enc_key: str,
        gmail_client_factory: GmailClientFactory,
    ) -> None:
        self._db = db
        self._token_enc_key = token_enc_key
        self._gmail_client_factory = gmail_client_factory

    def list_messages(
        self,
        *,
        current_user_id: int,
        account_id: int,
    ) -> list[AccountMessage]:
        account = self._db.execute(
            select(GoogleAccount).where(
                GoogleAccount.id == account_id,
                GoogleAccount.user_id == current_user_id,
            )
        ).scalar_one_or_none()
        if account is None:
            raise AccountNotFoundOrNotOwnedError("Account not found")

        if not account.token_encrypted:
            raise AccountTokenInvalidError("Account refresh token is missing.")

        try:
            refresh_token = decrypt_refresh_token(self._token_enc_key, account.token_encrypted)
        except TokenEncryptionError as exc:
            raise AccountTokenInvalidError("Account refresh token is invalid.") from exc

        try:
            gmail_client = self._gmail_client_factory.create(refresh_token=refresh_token)
        except GmailClientAuthError as exc:
            raise AccountTokenInvalidError("Failed to authenticate Gmail account.") from exc

        raw_messages = gmail_client.list_messages(max_results=10)
        return [self._to_account_message(m) for m in raw_messages[:10]]

    def _to_account_message(self, raw: dict) -> AccountMessage:
        payload = raw.get("payload", {}) or {}
        headers = payload.get("headers", []) or []
        return AccountMessage(
            id=str(raw.get("id", "")),
            subject=self._header(headers, "Subject"),
            from_=self._header(headers, "From"),
            snippet=str(raw.get("snippet", "")),
            date=self._date(raw, headers),
        )

    @staticmethod
    def _header(headers: list[dict], name: str) -> str:
        for header in headers:
            if header.get("name", "").lower() == name.lower():
                return str(header.get("value", ""))
        return ""

    @staticmethod
    def _date(raw: dict, headers: list[dict]) -> datetime:
        internal = raw.get("internalDate")
        if internal:
            try:
                return datetime.fromtimestamp(int(internal) / 1000, tz=UTC)
            except (TypeError, ValueError):
                pass

        date_header = AccountMessagesService._header(headers, "Date")
        if date_header:
            try:
                parsed = parsedate_to_datetime(date_header)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=UTC)
                return parsed.astimezone(UTC)
            except (TypeError, ValueError):
                pass

        return datetime.fromtimestamp(0, tz=UTC)
