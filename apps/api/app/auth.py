from __future__ import annotations

from uuid import uuid4

from fastapi import Request
from sqlalchemy.orm import Session

from .models import User


DEFAULT_LOCAL_USER_EMAIL_PREFIX = "local-user"


def _new_local_user_email() -> str:
    return f"{DEFAULT_LOCAL_USER_EMAIL_PREFIX}+{uuid4().hex}@localhost"


def get_or_create_current_user(request: Request, db: Session) -> User:
    session_user_id = request.session.get("user_id")
    if session_user_id is not None:
        existing = db.get(User, session_user_id)
        if existing is not None:
            return existing

    user = User(email=_new_local_user_email())
    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    return user
