# Task007 — README Normalization & Documentation Alignment

## Goal

Ensure all README and documentation files reflect the current architecture, security model, and development workflow.

This task is documentation-only. No application logic changes.

---

## Scope

Review and normalize:

* Root `README.md`
* `apps/api/README.md` (if exists)
* `apps/web/README.md` (if exists)

For documentation under `docs/`:

* Review `docs/architecture.md` and `docs/security.md` for alignment with the current implementation.
* Do **NOT** rewrite or restructure these files.
* Only add small clarifications where implementation has evolved (e.g., session isolation, strict OAuth state enforcement, production secret validation).

---

## Required Updates

### 1) Architecture consistency

Confirm docs accurately describe:

* Next.js App Router UI under `apps/web`
* Browser talks only to Next.js `/api/*` routes
* Next.js proxies requests to FastAPI and forwards:

  * cookies
  * `Set-Cookie`
  * status codes
  * redirect `Location` headers
* FastAPI under `apps/api`:

  * SessionMiddleware session boundary
  * strict OAuth callback state validation (required match + one-time consumption)
  * encrypted refresh token storage
  * multi-account per session user
* Shared core under `packages/core`
* CLI under `gmail_cleanup` remains functional

---

### 2) Environment variables

Document clearly (no secrets):

#### Backend (apps/api)

* `APP_ENV` (default `development`)
* `APP_SESSION_SECRET` (required + non-placeholder when `APP_ENV=production`)
* `GOOGLE_CLIENT_ID`
* `GOOGLE_CLIENT_SECRET`
* `GOOGLE_REDIRECT_URL`
* `TOKEN_ENC_KEY`
* `DATABASE_URL` (default sqlite path)

#### Frontend (apps/web)

* `FASTAPI_BASE_URL` (default `http://127.0.0.1:8000`)

---

### 3) Database documentation

Document:

* Default DB location: `apps/api/local.db`
* How to print DB URL:

```bash
PYTHONPATH=apps/api python -c "from app.settings import get_settings; print(get_settings().database_url)"
```

* How to reset DB:

  * Stop API
  * Delete `apps/api/local.db`
  * Restart API

* How to run migrations:

```bash
cd apps/api
alembic upgrade head
```

---

### 4) Local development instructions

Backend:

```bash
cd apps/api
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Testing:

```bash
python -m pytest -q
cd apps/web && npm run build
```

CLI check:

```bash
gmail-cleanup --help
```

---

### 5) Production security note

Document:

* `APP_ENV=production`
* `APP_SESSION_SECRET` must be set and must not be a placeholder value
* Session cookies use `https_only=True` when `APP_ENV=production`
* OAuth callback requires both query `state` and session `oauth_state` to exist and match
* OAuth callback consumes `oauth_state` once to block replay
* Refresh tokens are encrypted at rest using `TOKEN_ENC_KEY`

---

## Constraints

* Minimal, additive changes only.
* Do not remove useful existing content.
* Do not include secrets.
* Do not restructure repository.
* Output unified diff patch only.
* No code changes.

---

## Definition of Done

* Documentation matches current implementation.
* Instructions are correct and reproducible.
* `python -m pytest -q` passes.
* `cd apps/web && npm run build` succeeds.
* CLI still works: `gmail-cleanup --help`.

---

## Deliverables

* Updated doc files (as needed) via unified diff patch.
* Recommended commit message:
  `docs: normalize and update documentation for architecture and security hardening`
