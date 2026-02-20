from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.models import GoogleAccount, User


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


def test_accounts_missing_session_creates_new_user_not_first_existing(
    client: TestClient,
    testing_session_local: sessionmaker,
) -> None:
    with testing_session_local() as db:
        existing = User(email="existing@localhost")
        db.add(existing)
        db.commit()
        db.refresh(existing)

        db.add(
            GoogleAccount(
                user_id=existing.id,
                google_sub="existing-sub",
                email="existing@gmail.com",
                token_encrypted="encrypted",
                scopes="openid email profile",
                last_used_at=datetime.now(UTC),
            )
        )
        db.commit()

    response = client.get("/accounts")
    assert response.status_code == 200
    assert response.json() == {"accounts": []}

    with testing_session_local() as db:
        users = db.execute(select(User).order_by(User.id.asc())).scalars().all()
        assert len(users) == 2
        assert users[0].email == "existing@localhost"
        assert users[1].email.startswith("local-user+")


def test_accounts_invalid_session_user_id_creates_new_user_not_first_existing(
    client: TestClient,
    testing_session_local: sessionmaker,
) -> None:
    with testing_session_local() as db:
        existing = User(email="existing@localhost")
        db.add(existing)
        db.commit()
        db.refresh(existing)

        db.add(
            GoogleAccount(
                user_id=existing.id,
                google_sub="existing-sub",
                email="existing@gmail.com",
                token_encrypted="encrypted",
                scopes="openid email profile",
                last_used_at=datetime.now(UTC),
            )
        )
        db.commit()

    first = client.get("/accounts")
    assert first.status_code == 200
    assert first.json() == {"accounts": []}

    with testing_session_local() as db:
        local_user = db.execute(
            select(User).where(User.email.like("local-user+%@localhost")).order_by(User.id.desc()).limit(1)
        ).scalar_one()
        db.delete(local_user)
        db.commit()

    second = client.get("/accounts")
    assert second.status_code == 200
    assert second.json() == {"accounts": []}

    with testing_session_local() as db:
        users = db.execute(select(User).order_by(User.id.asc())).scalars().all()
        assert len(users) == 2
        assert users[0].email == "existing@localhost"
        assert users[1].email.startswith("local-user+")
