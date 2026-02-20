from __future__ import annotations

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import User


DEFAULT_LOCAL_USER_EMAIL = "local-user@localhost"


def get_or_create_current_user(request: Request, db: Session) -> User:
    session_user_id = request.session.get("user_id")
    if session_user_id is not None:
        existing = db.get(User, session_user_id)
        if existing is not None:
            return existing

    user = db.execute(select(User).order_by(User.id.asc()).limit(1)).scalar_one_or_none()
    if user is None:
        user = User(email=DEFAULT_LOCAL_USER_EMAIL)
        db.add(user)
        db.commit()
        db.refresh(user)

    request.session["user_id"] = user.id
    return user
