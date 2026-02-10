from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]  # safe for later (trash/label), still dry-run now


def _app_data_dir() -> Path:
    """
    Store token outside the repo to keep public repo clean.
    Windows: %APPDATA%/gmail-cleanup/
    macOS/Linux: ~/.config/gmail-cleanup/
    """
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "gmail-cleanup"
    return Path.home() / ".config" / "gmail-cleanup"


def credentials_path() -> Path:
    return _app_data_dir() / "credentials.json"


def token_path() -> Path:
    return _app_data_dir() / "token.json"


def ensure_app_dir() -> Path:
    d = _app_data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def ensure_credentials_file_in_app_dir(project_root_credentials: Path = Path("credentials.json")) -> Path:
    """
    If user has credentials.json in the current folder (local, ignored by git),
    copy it into the app data dir so the CLI keeps working from anywhere.
    """
    ensure_app_dir()
    dest = credentials_path()

    if dest.exists():
        return dest

    if project_root_credentials.exists():
        dest.write_bytes(project_root_credentials.read_bytes())
        return dest

    raise FileNotFoundError(
        "Could not find credentials.json. Put it next to the repo (it is gitignored) "
        "or copy it into the app data dir: "
        f"{dest}"
    )


def get_gmail_service():
    ensure_app_dir()
    cred_file = ensure_credentials_file_in_app_dir()
    tok_file = token_path()

    creds: Optional[Credentials] = None
    if tok_file.exists():
        creds = Credentials.from_authorized_user_file(str(tok_file), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(cred_file), SCOPES)
        creds = flow.run_local_server(port=0)

    # Save token outside repo
    tok_file.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)
