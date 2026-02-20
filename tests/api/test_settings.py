from __future__ import annotations

import pytest

import app.settings as settings_module


def test_get_settings_production_rejects_unset_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings_module, "_load_env", lambda: None)
    settings_module.get_settings.cache_clear()

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("APP_SESSION_SECRET", raising=False)

    with pytest.raises(
        ValueError,
        match="APP_SESSION_SECRET must be explicitly set to a non-placeholder value outside development.",
    ):
        settings_module.get_settings()

    settings_module.get_settings.cache_clear()


def test_get_settings_production_rejects_replace_placeholder_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings_module, "_load_env", lambda: None)
    settings_module.get_settings.cache_clear()

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_SESSION_SECRET", "replace-with-random-session-secret")

    with pytest.raises(
        ValueError,
        match="APP_SESSION_SECRET must be explicitly set to a non-placeholder value outside development.",
    ):
        settings_module.get_settings()

    settings_module.get_settings.cache_clear()


def test_get_settings_production_rejects_local_dev_placeholder_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings_module, "_load_env", lambda: None)
    settings_module.get_settings.cache_clear()

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_SESSION_SECRET", "local-dev-session-secret")

    with pytest.raises(
        ValueError,
        match="APP_SESSION_SECRET must be explicitly set to a non-placeholder value outside development.",
    ):
        settings_module.get_settings()

    settings_module.get_settings.cache_clear()


def test_get_settings_development_allows_placeholder_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings_module, "_load_env", lambda: None)
    settings_module.get_settings.cache_clear()

    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("APP_SESSION_SECRET", "replace-with-random-session-secret")

    settings = settings_module.get_settings()
    assert settings.app_env == "development"
    assert settings.app_session_secret == "replace-with-random-session-secret"

    settings_module.get_settings.cache_clear()
