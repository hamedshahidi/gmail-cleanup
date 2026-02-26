from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

import app.main as main_module
from app.schemas.messages import AccountMessage
from app.services.account_messages_service import AccountNotFoundOrNotOwnedError, AccountTokenInvalidError


class _StubMessagesService:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def list_messages(self, *, current_user_id: int, account_id: int) -> list[AccountMessage]:
        self.calls.append((current_user_id, account_id))
        return [
            AccountMessage(
                id="msg-1",
                subject="Hello",
                from_="sender@example.com",
                snippet="preview",
                date=datetime(2024, 1, 1, tzinfo=UTC),
            )
        ]


class _NotFoundMessagesService:
    def list_messages(self, *, current_user_id: int, account_id: int) -> list[AccountMessage]:
        raise AccountNotFoundOrNotOwnedError("missing")


class _InvalidTokenMessagesService:
    def list_messages(self, *, current_user_id: int, account_id: int) -> list[AccountMessage]:
        raise AccountTokenInvalidError("invalid token")


def test_account_messages_route_returns_response_model_shape(client: TestClient) -> None:
    stub = _StubMessagesService()
    main_module.app.dependency_overrides[main_module.get_account_messages_service] = lambda: stub
    try:
        response = client.get("/accounts/123/messages")
    finally:
        main_module.app.dependency_overrides.pop(main_module.get_account_messages_service, None)

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "msg-1",
            "subject": "Hello",
            "from": "sender@example.com",
            "snippet": "preview",
            "date": "2024-01-01T00:00:00Z",
        }
    ]
    assert len(stub.calls) == 1
    current_user_id, account_id = stub.calls[0]
    assert current_user_id > 0
    assert account_id == 123


def test_account_messages_route_returns_404_when_service_reports_missing_or_unowned(
    client: TestClient,
) -> None:
    main_module.app.dependency_overrides[main_module.get_account_messages_service] = (
        lambda: _NotFoundMessagesService()
    )
    try:
        response = client.get("/accounts/999/messages")
    finally:
        main_module.app.dependency_overrides.pop(main_module.get_account_messages_service, None)

    assert response.status_code == 404
    assert response.json() == {"detail": "Account not found"}


def test_account_messages_route_returns_400_when_service_reports_invalid_token(
    client: TestClient,
) -> None:
    main_module.app.dependency_overrides[main_module.get_account_messages_service] = (
        lambda: _InvalidTokenMessagesService()
    )
    try:
        response = client.get("/accounts/999/messages")
    finally:
        main_module.app.dependency_overrides.pop(main_module.get_account_messages_service, None)

    assert response.status_code == 400
    assert response.json() == {"detail": "Account token invalid"}
