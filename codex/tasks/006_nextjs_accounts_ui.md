# Task 005: Next.js UI (Option B Proxy)

## Goal
Implement the MVP Next.js UI in `apps/web` with Option B proxy architecture:
- Browser only talks to Next.js.
- Next.js `/api/*` routes proxy to FastAPI.
- `FASTAPI_BASE_URL` env var controls backend base URL; default `http://127.0.0.1:8000`.

## Constraints (non-negotiable)
- Public repo: NO secrets committed (no `.env`, `credentials.json`, `token.json`, DB files).
- Keep Python CLI unchanged (`gmail-cleanup = gmail_cleanup.cli:app`).
- Minimal, incremental changes; prefer additive changes.
- Tests MUST NOT call Google endpoints.

## Scope (MVP)
### A) Next.js app
Create a real Next.js app under `apps/web` (not placeholder).
- Use the simplest routing approach (Pages Router is fine).
- Provide `/accounts` page with:
  - fetch accounts via `GET /api/accounts`
  - list connected Gmail accounts (email)
  - “Connect Gmail account” button navigates to `/api/oauth/google/start`
  - basic loading + error states
- Home (`/`) redirects to `/accounts`.

### B) Next.js proxy API routes
Add API route handlers under `apps/web/pages/api`:
- `/api/health` -> proxy to FastAPI `/health`
- `/api/accounts` -> proxy to FastAPI `/accounts`
- `/api/oauth/google/start` -> proxy to FastAPI `/oauth/google/start`
  - Must preserve upstream redirects (`Location` header + 30x status)
  - Must preserve cookies (forward `Cookie` header; forward `Set-Cookie` header(s))
- Optional:
  - `/api/oauth/google/callback` -> proxy to FastAPI `/oauth/google/callback`
  - If not implemented, ensure local OAuth can still work (redirect URIs consistent).

### C) Env config and secrets
- Add `FASTAPI_BASE_URL` env var for Next.js server-side use.
- Default: `http://127.0.0.1:8000`
- Commit only `.env.example`, never `.env` or `.env.local`.

### D) Docs
Add `apps/web/README.md` explaining local run:
- Start FastAPI on `:8000`
- Start Next.js on `:3000`
- Visit `http://localhost:3000/accounts`

## Acceptance Criteria
- `apps/web` is a functioning Next.js app.
- `/accounts` loads accounts from FastAPI through Next.js proxy (`/api/accounts`).
- “Connect Gmail account” goes to `/api/oauth/google/start` and browser follows redirect to Google.
- Cookie session from FastAPI is preserved across proxy calls (Set-Cookie forwarded).
- No secrets added to repo.
- Tests do not call Google endpoints.
- Existing Python tests still pass: `python -m pytest -q`
- CLI still works: `gmail-cleanup --help`
