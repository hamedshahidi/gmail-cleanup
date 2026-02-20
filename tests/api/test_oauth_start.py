from __future__ import annotations

from fastapi.testclient import TestClient


def test_oauth_google_start_returns_500_without_credentials(client: TestClient) -> None:
    response = client.get("/oauth/google/start")
    assert response.status_code == 500
    assert response.json() == {"detail": "Google OAuth is not configured."}
