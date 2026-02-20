from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./apps/api/local.db"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_url: str = "http://localhost:8000/oauth/google/callback"
    token_enc_key: str = ""
    app_session_secret: str = "local-dev-session-secret"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _load_env()
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./apps/api/local.db"),
        google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
        google_redirect_url=os.getenv("GOOGLE_REDIRECT_URL", "http://localhost:8000/oauth/google/callback"),
        token_enc_key=os.getenv("TOKEN_ENC_KEY", ""),
        app_session_secret=os.getenv("APP_SESSION_SECRET", "local-dev-session-secret"),
    )
