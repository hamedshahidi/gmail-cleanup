# apps/api

FastAPI service for OAuth account linking/session management used by `apps/web`.

## What this app does
- Starts Google OAuth (`GET /oauth/google/start`).
- Handles OAuth callback and stores encrypted refresh token (`GET /oauth/google/callback`).
- Lists linked Google accounts for the current session user (`GET /accounts`).
- Disconnects a linked account (`DELETE /accounts/{account_id}`).
- Clears session (`POST /logout`).

## Local setup
1. From repo root, create `.env` from `.env.example`.
2. Set required values:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URL` (default: `http://localhost:8000/oauth/google/callback`)
   - `TOKEN_ENC_KEY` (Fernet key)
   - `APP_SESSION_SECRET`
3. Install dependencies (repo root):
   ```bash
   pip install -e .[dev]
   ```

## Environment Variables
- `DATABASE_URL` (optional, default: `sqlite:///apps/api/local.db`)
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URL` (default: `http://localhost:8000/oauth/google/callback`)
- `TOKEN_ENC_KEY` (Fernet key for refresh token encryption)
- `APP_ENV` (`development` default)
- `APP_SESSION_SECRET`:
  - development: default placeholder is allowed
  - non-development: must be explicitly set to a non-placeholder value

## Database (Local Development)
- Default DB path: `apps/api/local.db`.
- `DATABASE_URL` defaults to `sqlite:///apps/api/local.db` via `app/settings.py`:
  - `repo_root = Path(__file__).resolve().parents[3]`
  - `db_path = repo_root / "apps" / "api" / "local.db"`
  - `default_database_url = f"sqlite:///{db_path.as_posix()}"`
- Print the effective DB URL:
  ```bash
  PYTHONPATH=apps/api python -c "from app.settings import get_settings; print(get_settings().database_url)"
  ```
- Reset local DB:
  1. Stop the API server.
  2. Delete `apps/api/local.db`.
  3. Restart the API server.
- Run migrations:
  ```bash
  cd apps/api
  alembic upgrade head
  ```
- Note: `apps/api/local.db` is local development storage only and should not be committed.

## Run
```bash
uvicorn apps.api.app.main:app --reload --port 8000
```

## OAuth local notes
- Google OAuth redirect URI must include: `http://localhost:8000/oauth/google/callback`.
- If your Google OAuth app is in testing mode, add your Gmail account under OAuth test users in Google Cloud Console.
- The frontend (`apps/web`) should call only Next.js `/api/*` routes, which proxy to this API.
- Callback state handling is strict:
  - both query `state` and session `oauth_state` must exist and match
  - `oauth_state` is consumed once (replay fails)

## Session and Token Security Notes
- FastAPI uses `SessionMiddleware` with:
  - `same_site=lax`
  - `max_age=7 days`
  - `https_only=True` when `APP_ENV=production`
- Google refresh tokens are encrypted before persistence using `TOKEN_ENC_KEY`.

## Tests
```bash
pytest -q
```
- API tests under `tests/api` use a temporary SQLite DB and do not call Google endpoints.
