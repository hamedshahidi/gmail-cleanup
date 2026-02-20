from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.settings import Settings


def _settings_with_google() -> Settings:
    return Settings(
        database_url="sqlite:///unused-by-test-override.db",
        google_client_id="test-google-client-id",
        google_client_secret="test-google-client-secret",
        google_redirect_url="http://testserver/oauth/google/callback",
        token_enc_key="unused-in-mocked-tests",
        app_session_secret="test-session-secret",
    )


def _install_mock_oauth(monkeypatch: pytest.MonkeyPatch) -> None:
    class StartFlow:
        def authorization_url(self, **_kwargs):
            return ("https://accounts.google.com/o/oauth2/v2/auth", "expected-state")

    class CallbackFlow:
        def __init__(self) -> None:
            self.oauth2session = SimpleNamespace(scope=["placeholder"])
            self.credentials = SimpleNamespace(
                refresh_token="refresh-token",
                scopes=["openid", "email", "profile"],
                token="access-token",
            )

        def fetch_token(self, code: str) -> None:
            assert code

    def _build_google_flow(_settings, state: str | None = None):
        if state is None:
            return StartFlow()
        return CallbackFlow()

    monkeypatch.setattr(main_module, "build_google_flow", _build_google_flow)
    monkeypatch.setattr(main_module, "fetch_google_userinfo", lambda _token: {"sub": "sub-123", "email": "user@test.local"})
    monkeypatch.setattr(main_module, "encrypt_refresh_token", lambda _key, token: f"enc:{token}")


def test_oauth_callback_rejects_missing_session_state(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _should_not_call_flow(*_args, **_kwargs):
        raise AssertionError("build_google_flow should not be called when oauth_state is missing")

    monkeypatch.setattr(main_module, "build_google_flow", _should_not_call_flow)

    response = client.get("/oauth/google/callback?code=test-code&state=expected-state")
    assert response.status_code == 400
    assert response.json() == {"detail": "OAuth state missing or mismatch."}


def test_oauth_callback_rejects_missing_query_state(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main_module, "settings", _settings_with_google())
    _install_mock_oauth(monkeypatch)

    start = client.get("/oauth/google/start", follow_redirects=False)
    assert start.status_code == 302

    callback = client.get("/oauth/google/callback?code=test-code")
    assert callback.status_code == 400
    assert callback.json() == {"detail": "OAuth state missing or mismatch."}


def test_oauth_callback_rejects_state_mismatch(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main_module, "settings", _settings_with_google())
    _install_mock_oauth(monkeypatch)

    start = client.get("/oauth/google/start", follow_redirects=False)
    assert start.status_code == 302

    callback = client.get("/oauth/google/callback?code=test-code&state=wrong-state")
    assert callback.status_code == 400
    assert callback.json() == {"detail": "OAuth state missing or mismatch."}


def test_oauth_callback_rejects_replay_after_state_consumption(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main_module, "settings", _settings_with_google())
    _install_mock_oauth(monkeypatch)

    start = client.get("/oauth/google/start", follow_redirects=False)
    assert start.status_code == 302

    first = client.get("/oauth/google/callback?code=test-code&state=expected-state", follow_redirects=False)
    assert first.status_code == 302

    replay = client.get("/oauth/google/callback?code=test-code&state=expected-state")
    assert replay.status_code == 400
    assert replay.json() == {"detail": "OAuth state missing or mismatch."}
