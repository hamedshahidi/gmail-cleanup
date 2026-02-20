from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.models import User


def test_accounts_returns_empty_and_creates_local_user(
    client: TestClient,
    testing_session_local: sessionmaker,
) -> None:
    response = client.get("/accounts")
    assert response.status_code == 200
    assert response.json() == {"accounts": []}
    assert client.cookies.get("session") is not None

    with testing_session_local() as db:
        users = db.execute(select(User)).scalars().all()
        assert len(users) == 1

    second = client.get("/accounts")
    assert second.status_code == 200
    assert second.json() == {"accounts": []}

    with testing_session_local() as db:
        users = db.execute(select(User)).scalars().all()
        assert len(users) == 1
