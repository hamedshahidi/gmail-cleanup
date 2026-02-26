# gmail-cleanup

A **safe, local-first Gmail cleanup system** designed for power users who want to clean their inbox **without accidents**.

This project contains:

* ✅ Safe Gmail CLI (`gmail-cleanup`)
* ✅ FastAPI backend (`apps/api`)
* ✅ Next.js frontend (`apps/web`)
* ✅ Shared cleanup core
* ✅ Deterministic task runner (`task`)

Core philosophy:

> **You should never delete emails you haven’t reviewed.**

Default workflow:

```
query → label → export → trash
```

No background service.
No cloud storage of emails.
No deletion without explicit confirmation.

---

# Project Structure

```
apps/
  api/        → FastAPI backend
  web/        → Next.js frontend
gmail_cleanup/ → Original CLI (must remain functional)
packages/
codex/tasks/
docs/
pyproject.toml
Taskfile.yml
```

Architecture:

```
Browser
  → Next.js (/api/*)
    → FastAPI
      → Shared Core
        → Gmail API
```

Browser **never talks directly to FastAPI**.

---

# Requirements

* Python 3.10+
* Node 18+
* npm
* A Google account
* Google Cloud project with Gmail API enabled

---

# 🚀 First-Time Setup (One Command)

From repo root:

```bash
task up
```

That’s it.

This will:

* Create `.venv` (if missing)
* Install Python dependencies from `pyproject.toml`
* Install frontend dependencies
* Install Playwright browsers
* Start:

  * API → [http://127.0.0.1:8000](http://127.0.0.1:8000)
  * Web → [http://localhost:3000](http://localhost:3000)

No manual virtualenv activation required.
No global `uvicorn` required.

---

# Development Commands

## Start everything

```bash
task up
```

## Run tests

```bash
task test
```

Runs:

* Backend tests (no Google endpoints)
* Web build
* Playwright E2E tests (mocked `/api/*`)

## Build frontend

```bash
task build:web
```

---

# CLI Usage (Still Fully Supported)

The original CLI remains fully functional.

## Install via pipx (recommended)

```bash
pipx install gmail-cleanup
```

## Development usage (inside repo)

```bash
.venv/Scripts/python -m gmail_cleanup --help
```

or after activation:

```bash
gmail-cleanup --help
```

---

# Environment Variables

## Backend (repo root environment)

Required for OAuth:

* `GOOGLE_CLIENT_ID`
* `GOOGLE_CLIENT_SECRET`
* `TOKEN_ENC_KEY`

Optional:

* `DATABASE_URL`
* `GOOGLE_REDIRECT_URL`
* `APP_ENV`
* `APP_SESSION_SECRET`

Defaults:

* SQLite database stored at:

```
apps/api/local.db
```

⚠️ Never commit:

* `.env`
* `local.db`
* `credentials.json`
* `token.json`

---

## Frontend (`apps/web/.env.local`)

Optional:

* `FASTAPI_BASE_URL`

  * Default: `http://127.0.0.1:8000`

---

# Database (Local Development)

Default:

```
apps/api/local.db
```

To reset:

1. Stop API
2. Delete `apps/api/local.db`
3. Restart `task up`

Run migrations manually:

```bash
cd apps/api
alembic upgrade head
```

---

# Google OAuth Setup (One-Time)

### 1. Create Google Cloud Project

* Google Cloud Console → New Project

### 2. Enable Gmail API

* APIs & Services → Library → Enable Gmail API

### 3. Create OAuth Client

* APIs & Services → Credentials
* OAuth Client ID
* Type: Desktop App
* Download `credentials.json`

### 4. Place credentials file

Windows:

```
C:\Users\<YOU>\AppData\Roaming\gmail-cleanup\credentials.json
```

macOS/Linux:

```
~/.config/gmail-cleanup/credentials.json
```

Never commit this file.

---

# Verify CLI Setup

```bash
gmail-cleanup doctor
```

This:

* Shows expected paths
* Checks for credentials
* Makes no API calls

---

# Core Workflow (Safe Cleanup)

## 1. Preview (Dry-Run)

```bash
gmail-cleanup query --from team@news.bookbeat.com --older-than 30d --sample 5
```

Shows counts and sample messages.

---

## 2. Stage with Label

```bash
gmail-cleanup label \
  --from team@news.bookbeat.com \
  --older-than 30d \
  --target-label cleanup/candidates
```

Does not delete anything.

---

## 3. Export Report (Optional)

```bash
gmail-cleanup export \
  --label cleanup/candidates \
  --out reports/bookbeat.csv
```

---

## 4. Trash (Guarded & Recoverable)

```bash
gmail-cleanup trash \
  --label cleanup/candidates \
  --execute
```

Safety checks:

* Label must start with `cleanup/`
* Requires `--execute`
* Requires typed confirmation
* Moves to Trash (recoverable)

---

# Safety Guarantees

* ❌ No deletion without label
* ❌ No deletion without `--execute`
* ❌ No deletion without typed confirmation
* ❌ No permanent delete
* ✅ Trash is recoverable

Safety enforcement lives server-side and in shared core.

---

# Production Behavior Notes

* Session cookies hardened when `APP_ENV=production`
* OAuth state validation enforced
* Refresh tokens encrypted at rest
* No secrets committed to repository

---

# Testing Policy

* Tests never call Google endpoints
* Playwright mocks `/api/*`
* CLI safety rules tested
* `task test` must pass before merge

---

# Public Repository Rules

This repository:

* Contains no secrets
* Contains no credentials
* Contains no tokens
* Contains no database files
* Is safe to clone publicly

Only `.env.example` files may be committed.

---

# Roadmap

* Permanent delete (extra confirmation)
* Attachment filters
* Label cleanup helpers
* Undo helpers
* Cloud deployment hardening
* CI pipeline automation

---

# Philosophy

Inbox cleanup should be:

* intentional
* reversible
* inspectable
* safe by default

If a tool makes it easy to delete the wrong thing, it’s a bad tool.

This one tries hard not to.
