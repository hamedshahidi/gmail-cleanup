from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import GoogleAccount
from ..schemas.messages import AccountMessage


class AccountNotFoundOrNotOwnedError(LookupError):
    pass


class AccountMessagesService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_messages(
        self,
        *,
        current_user_id: int,
        account_id: int,
    ) -> list[AccountMessage]:
        account = self._db.execute(
            select(GoogleAccount.id).where(
                GoogleAccount.id == account_id,
                GoogleAccount.user_id == current_user_id,
            )
        ).scalar_one_or_none()
        if account is None:
            raise AccountNotFoundOrNotOwnedError("Account not found")
        return []
