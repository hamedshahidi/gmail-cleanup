from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.main as main_module
from app.db import Base
from app.settings import Settings


@pytest.fixture()
def testing_session_local(tmp_path: pytest.TempPathFactory) -> Generator[sessionmaker, None, None]:
    db_path = tmp_path / "api-test.db"
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False}, future=True)
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session, future=True)

    Base.metadata.create_all(bind=engine)
    try:
        yield testing_session
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(
    monkeypatch: pytest.MonkeyPatch,
    testing_session_local: sessionmaker,
) -> Generator[TestClient, None, None]:
    test_settings = Settings(
        database_url="sqlite:///unused-by-test-override.db",
        google_client_id="",
        google_client_secret="",
        google_redirect_url="http://testserver/oauth/google/callback",
        token_enc_key="",
        app_session_secret="test-session-secret",
    )
    monkeypatch.setattr(main_module, "settings", test_settings)

    def _override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    main_module.app.dependency_overrides[main_module.get_db] = _override_get_db
    try:
        with TestClient(main_module.app) as test_client:
            yield test_client
    finally:
        main_module.app.dependency_overrides.clear()
