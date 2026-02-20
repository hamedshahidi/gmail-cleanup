from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .auth import get_or_create_current_user
from .db import get_db
from .models import GoogleAccount
from .oauth import build_google_flow, fetch_google_userinfo
from .security import TokenEncryptionError, encrypt_refresh_token
from .settings import get_settings


settings = get_settings()
app = FastAPI(title="gmail-cleanup API")
app.add_middleware(SessionMiddleware, secret_key=settings.app_session_secret)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/oauth/google/start")
def oauth_google_start(request: Request) -> RedirectResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured.")

    flow = build_google_flow(settings)
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["oauth_state"] = state
    return RedirectResponse(url=auth_url, status_code=302)


@app.get("/oauth/google/callback")
def oauth_google_callback(
    request: Request,
    code: str = Query(...),
    state: str | None = Query(default=None),
    scope: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> JSONResponse:
    expected_state = request.session.get("oauth_state")
    if expected_state and state != expected_state:
        raise HTTPException(status_code=400, detail="OAuth state mismatch.")

    flow = build_google_flow(settings, state=state)

    # oauthlib can raise on "scope changed" even when Google returns equivalent scopes.
    # Accept the granted scopes returned by Google.
    flow.oauth2session.scope = None

    flow.fetch_token(code=code)
    creds = flow.credentials

    refresh_token = creds.refresh_token
    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail="Google did not return a refresh token. Reconnect with consent prompt.",
        )

    userinfo = fetch_google_userinfo(creds.token)
    google_sub = userinfo.get("sub")
    email = userinfo.get("email")
    if not google_sub or not email:
        raise HTTPException(status_code=400, detail="Google userinfo missing sub/email.")

    current_user = get_or_create_current_user(request, db)
    scopes = " ".join(creds.scopes or []) or (scope or "")

    try:
        encrypted = encrypt_refresh_token(settings.token_enc_key, refresh_token)
    except TokenEncryptionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    account = db.execute(
        select(GoogleAccount).where(
            GoogleAccount.user_id == current_user.id,
            GoogleAccount.google_sub == google_sub,
        )
    ).scalar_one_or_none()

    if account is None:
        account = GoogleAccount(
            user_id=current_user.id,
            google_sub=google_sub,
            email=email,
            token_encrypted=encrypted,
            scopes=scopes,
            last_used_at=datetime.now(UTC),
        )
        db.add(account)
    else:
        account.email = email
        account.token_encrypted = encrypted
        account.scopes = scopes
        account.last_used_at = datetime.now(UTC)

    db.commit()
    db.refresh(account)

    return RedirectResponse(url="http://localhost:3000/accounts", status_code=302)


@app.get("/accounts")
def list_accounts(request: Request, db: Session = Depends(get_db)) -> dict[str, list[dict]]:
    current_user = get_or_create_current_user(request, db)
    accounts = db.execute(
        select(GoogleAccount)
        .where(GoogleAccount.user_id == current_user.id)
        .order_by(GoogleAccount.created_at.asc())
    ).scalars().all()

    return {
        "accounts": [
            {
                "id": a.id,
                "google_sub": a.google_sub,
                "email": a.email,
                "scopes": a.scopes,
                "created_at": a.created_at.isoformat(),
                "last_used_at": a.last_used_at.isoformat() if a.last_used_at else None,
            }
            for a in accounts
        ]
    }


@app.post("/logout")
def logout(request: Request) -> JSONResponse:
    request.session.clear()
    resp = JSONResponse({"logged_out": True})
    resp.delete_cookie("session")
    return resp


@app.delete("/accounts/{account_id}")
def delete_account(account_id: int, request: Request, db: Session = Depends(get_db)) -> dict[str, bool]:
    current_user = get_or_create_current_user(request, db)

    account = db.execute(
        select(GoogleAccount).where(
            GoogleAccount.id == account_id,
            GoogleAccount.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(account)
    db.commit()
    return {"deleted": True}
