# Task 004: FastAPI backend skeleton + OAuth connect + accounts (local MVP, cloud-shaped)

## Goal
Create a runnable FastAPI API in apps/api with SQLite storage and Google OAuth connect flow to support multiple connected Gmail accounts.

## Constraints
- Additive changes only (do not break CLI).
- Reuse existing Gmail auth/service creation logic where possible.
- No secrets in repo. Use env vars + templates only.
- Store refresh tokens encrypted at rest using TOKEN_ENC_KEY from env.
- Local DB is SQLite for MVP; cloud will later switch to Postgres via DATABASE_URL.

## Work
1) Scaffold FastAPI app in apps/api:
   - apps/api/app/main.py with FastAPI instance
   - GET /health endpoint

2) Add configuration:
   - apps/api/app/settings.py reading env vars:
     - DATABASE_URL (default sqlite file under repo or app-data; choose repo-local for now but gitignored)
     - GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
     - GOOGLE_REDIRECT_URL (e.g. http://localhost:8000/oauth/google/callback)
     - TOKEN_ENC_KEY
     - APP_SESSION_SECRET
   - Add .env.example (template only) at repo root (or apps/api)

3) Add DB models + migrations:
   - Use SQLAlchemy + Alembic
   - Tables:
     - users (id, email, created_at)
     - google_accounts (id, user_id, google_sub, email, token_encrypted, scopes, created_at, last_used_at)
   - Create initial migration

4) Minimal session/auth for local MVP:
   - Implement a simple cookie-based session to identify a single local user
   - For MVP: create/get a default local user record if none exists

5) OAuth connect flow:
   - GET /oauth/google/start -> returns redirect to Google auth URL (include prompt=consent, access_type=offline)
   - GET /oauth/google/callback -> exchange code for tokens, fetch userinfo (sub + email), store/update google_accounts row (encrypted refresh token)
   - Ensure multiple accounts can be connected

6) Accounts endpoint:
   - GET /accounts -> list connected google accounts for current user

## Acceptance criteria
- `uvicorn apps.api.app.main:app --reload` runs (or equivalent module path)
- /health returns ok
- OAuth start produces a Google URL
- Callback stores account in DB and /accounts lists it
- No secrets committed; local DB file is gitignored
