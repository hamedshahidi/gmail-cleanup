# Task 004.1: Add MVP-level FastAPI tests (no real Google calls)

## Goal
Add a minimal but solid test suite for the FastAPI app:
- health endpoint
- accounts endpoint behavior
- oauth start failure when not configured
- token encryption unit test

## Constraints
- Tests must not call real Google endpoints.
- Tests must not require real OAuth credentials.
- Use a temporary SQLite DB for tests (in-memory or temp file).
- Keep production code changes minimal.
- Ensure session middleware is present and stable in tests.

## Work
1) Add test dependencies to pyproject.toml (dev extras preferred):
   - pytest
   - httpx (required by FastAPI TestClient in newer stacks)
2) Add tests under tests/api/:
   - test_health.py:
     - GET /health returns 200 and {"status":"ok"}
   - test_accounts.py:
     - GET /accounts returns {"accounts": []} on fresh DB
     - Ensure it creates/uses a default local user session
   - test_oauth_start.py:
     - With empty GOOGLE_CLIENT_ID/SECRET, GET /oauth/google/start returns 500
3) Add unit test for token encryption in tests/api/test_security.py:
   - encrypt then decrypt returns original refresh token
   - invalid key raises TokenEncryptionError
4) Provide a test fixture in tests/conftest.py (or tests/api/conftest.py) that:
   - creates a FastAPI TestClient
   - overrides get_settings() for tests (use empty oauth creds for oauth start test; set session secret; set DB URL to sqlite)
   - ensures a clean DB per test run (create tables)
   - does not depend on alembic migrations (Base.metadata.create_all ok for unit tests)

## Acceptance criteria
- `pytest -q` passes locally.
- Tests run without any .env values.
- No network calls are made.
