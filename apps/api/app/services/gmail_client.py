from __future__ import annotations

from typing import Protocol

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..oauth import OAUTH_SCOPES


class GmailClient(Protocol):
    def list_messages(self, *, max_results: int) -> list[dict]:
        ...


class GmailClientAuthError(ValueError):
    pass


class GmailApiClient:
    def __init__(self, service: object) -> None:
        self._service = service

    def list_messages(self, *, max_results: int) -> list[dict]:
        listing = (
            self._service.users()
            .messages()
            .list(userId="me", maxResults=max_results)
            .execute()
        )
        refs = listing.get("messages", []) or []
        messages: list[dict] = []
        for ref in refs:
            message_id = ref.get("id")
            if not message_id:
                continue
            message = (
                self._service.users()
                .messages()
                .get(
                    userId="me",
                    id=message_id,
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                )
                .execute()
            )
            messages.append(message)
        return messages


class GmailClientFactory:
    def __init__(self, *, client_id: str, client_secret: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    def create(self, *, refresh_token: str) -> GmailClient:
        try:
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self._client_id,
                client_secret=self._client_secret,
                scopes=OAUTH_SCOPES,
            )
            creds.refresh(Request())
            service = build("gmail", "v1", credentials=creds, cache_discovery=False)
            return GmailApiClient(service)
        except (HttpError, ValueError) as exc:
            raise GmailClientAuthError("Failed to authenticate Gmail client.") from exc
