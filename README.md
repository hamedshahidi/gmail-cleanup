# gmail-cleanup

A **safe, local-first Gmail cleanup CLI** for power users who want to clean their inbox **without accidents**.

This tool is designed around a simple idea:

> **You should never delete emails you haven’t reviewed.**

So the default workflow is:

```
query → label → export → trash
```

No cloud service.
No data stored outside your machine.
No deletion without explicit confirmation.

---

## What this tool is

* A **local CLI** that talks directly to the Gmail API
* Runs entirely on **your computer**
* Uses **Google OAuth** (same as Gmail apps)
* Designed to be **safe by default**
* Open-source, transparent, auditable

## What this tool is NOT

* ❌ Not a web app
* ❌ Not a background service
* ❌ Not a “one-click delete everything” script
* ❌ Does not store or send your emails anywhere except Google

---

## Requirements

* Python **3.10+**
* A Google account (Gmail)
* A Google Cloud project with Gmail API enabled

---

## Installation

### Recommended (isolated install)

```bash
pipx install gmail-cleanup
```

### Development / local clone

```bash
git clone https://github.com/hamedshahidi/gmail-cleanup.git
cd gmail-cleanup
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
pip install -e .
```

---

## Monorepo Architecture

`Next.js (apps/web) -> FastAPI (apps/api) -> Gmail APIs`

- Browser talks only to Next.js `/api/*`.
- Next.js route handlers proxy to FastAPI and forward cookies / `Set-Cookie`.
- FastAPI uses `SessionMiddleware` for session state and stores encrypted Google refresh tokens.

## Environment Variables

Backend (`.env` at repo root):
- `DATABASE_URL` (optional, default: `sqlite:///apps/api/local.db`)
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URL` (default: `http://localhost:8000/oauth/google/callback`)
- `TOKEN_ENC_KEY` (Fernet key used for refresh token encryption)
- `APP_ENV` (`development` by default)
- `APP_SESSION_SECRET` (required and must be non-placeholder when `APP_ENV != development`)

Frontend (`apps/web/.env.local`):
- `FASTAPI_BASE_URL` (optional, default: `http://127.0.0.1:8000`)

## Database (Local Development)

- Default DB path: `apps/api/local.db`.
- `DATABASE_URL` defaults to `sqlite:///apps/api/local.db` via `apps/api/app/settings.py`:
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

## Local Development (API + Web)

1. Start API from repo root:
   ```bash
   uvicorn apps.api.app.main:app --reload --port 8000
   ```
2. In a second terminal:
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```
3. Open `http://localhost:3000/accounts`.

---

## Testing

- Backend tests:
  ```bash
  pytest -q
  ```
- Frontend build verification:
  ```bash
  cd apps/web
  npm run build
  ```

## Production Behavior Notes

- Session hardening:
  - `APP_ENV=production` enables secure session cookies (`https_only=True`) in FastAPI.
  - `APP_SESSION_SECRET` must be explicitly set to a non-placeholder value outside development.
  - Session cookies use `same_site=lax` and a max age of 7 days.
- OAuth callback enforces strict `state` validation and one-time `oauth_state` consumption.
- Refresh tokens are stored encrypted at rest in the API database.

---

## Google OAuth setup (one time)

### 1. Create Google Cloud project

* Go to Google Cloud Console
* Create a new project (any name)

### 2. Enable Gmail API

* APIs & Services → Library
* Search **Gmail API**
* Enable

### 3. Create OAuth client

* APIs & Services → Credentials
* Create Credentials → OAuth Client ID
* Application type: **Desktop app**
* Download `credentials.json`

### 4. Put `credentials.json` in the app data folder

On **Windows**:

```
C:\Users\<YOU>\AppData\Roaming\gmail-cleanup\credentials.json
```

(macOS / Linux use `~/.config/gmail-cleanup/`)

The file is **never committed** to this repo.

---

## Verify setup

```bash
gmail-cleanup doctor
```

This will:

* Show expected paths
* Check if credentials/token exist
* Explain how to fix missing pieces
* Make **no API calls**

---

## Core workflow (recommended)

### 1. Preview with `query` (dry-run)

```bash
gmail-cleanup query --from team@news.bookbeat.com --older-than 30d --sample 5
```

Shows:

* total count
* with / without attachments
* sample subjects + dates

No changes are made.

---

### 2. Stage candidates with `label`

```bash
gmail-cleanup label \
  --from team@news.bookbeat.com \
  --older-than 30d \
  --target-label cleanup/candidates
```

* Applies a Gmail label
* **Does not delete anything**
* Lets you review messages directly in Gmail UI

---

### 3. Export a report (optional but recommended)

```bash
gmail-cleanup export \
  --label cleanup/candidates \
  --out reports/bookbeat.csv \
  --limit 200
```

Exports:

* message id
* date
* from
* to
* subject

Good for auditing before destructive actions.

---

### 4. Trash (recoverable, guarded)

```bash
gmail-cleanup trash \
  --label cleanup/candidates \
  --execute
```

Safety checks:

* Only allows labels starting with `cleanup/`
* Shows counts + samples
* Requires `--execute`
* Requires typed confirmation: `TRASH <count>`
* Moves to **Trash** (recoverable)

---

## Commands overview

```text
gmail-cleanup query   # preview counts + samples (dry-run)
gmail-cleanup label   # apply staging labels
gmail-cleanup export  # export CSV / JSON reports
gmail-cleanup trash   # move labeled emails to Trash
gmail-cleanup doctor  # diagnose local setup
```

Run `--help` on any command for details.

---

## Safety guarantees

* ❌ No deletion without a label
* ❌ No deletion without `--execute`
* ❌ No deletion without typed confirmation
* ❌ No permanent delete (yet)
* ✅ Trash is recoverable via Gmail

This tool is intentionally conservative.

---

## File locations (important)

Nothing sensitive is stored in the repo.

| File             | Location                      |
| ---------------- | ----------------------------- |
| credentials.json | App data folder               |
| token.json       | App data folder               |
| reports          | Local folder (ignored by git) |

---

## Roadmap (planned)

* Permanent delete (opt-in, extra confirmation)
* Attachment size / type filters
* Label cleanup helpers
* Config file support
* Batch undo helpers

---

## License

MIT — do whatever you want, responsibly.

---

## Philosophy

Inbox cleanup should be:

* intentional
* reversible
* inspectable

If a tool makes it easy to delete the wrong thing, it’s a bad tool.

This one tries hard not to.
