from __future__ import annotations

import json
from urllib.request import Request, urlopen

from google_auth_oauthlib.flow import Flow

from gmail_cleanup.gmail import SCOPES as GMAIL_SCOPES

from .settings import Settings


OAUTH_SCOPES = [*GMAIL_SCOPES, "openid", "email", "profile"]


def _client_config(settings: Settings) -> dict:
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def build_google_flow(settings: Settings, state: str | None = None) -> Flow:
    flow = Flow.from_client_config(_client_config(settings), scopes=OAUTH_SCOPES, state=state)
    flow.redirect_uri = settings.google_redirect_url
    return flow


def fetch_google_userinfo(access_token: str) -> dict:
    req = Request(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    with urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))
