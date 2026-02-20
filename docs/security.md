# Security and Secret Handling

This repository is intended to stay public-safe.

## Do not commit secrets

Never commit any of the following:

- `credentials.json`
- `token.json`
- `.env` files containing secrets
- OAuth client secrets, API keys, access tokens, refresh tokens

## Where secrets belong

For this project, Gmail OAuth files must be stored in app-data, not in git-tracked files:

- Windows: `%APPDATA%/gmail-cleanup/`
- macOS/Linux: `~/.config/gmail-cleanup/`

Expected files:

- `credentials.json`
- `token.json`

## Local repo safety

The root `.gitignore` blocks common local secret and database files, including:

- `credentials.json`
- `token.json`
- `*.env`, `.env`, `.env.*`
- `*.db`, `*.sqlite`, `*.sqlite3`

## API session and OAuth hardening

- FastAPI uses `SessionMiddleware` with:
  - `same_site=lax`
  - `max_age=7 days`
  - `https_only=True` when `APP_ENV=production`
- `APP_ENV` defaults to `development`.
- Outside development, `APP_SESSION_SECRET` must be set and cannot be a placeholder value.
- OAuth callback requires query `state` and session `oauth_state` to both exist and match.
- OAuth callback consumes `oauth_state` once to block replay.
- Google refresh tokens are encrypted at rest using `TOKEN_ENC_KEY`.

## If a secret was committed

1. Revoke or rotate the leaked credential immediately in the provider console.
2. Remove the file from tracking:
   - `git rm --cached <path-to-secret>`
   - `git commit -m "stop tracking secret file"`
3. If already pushed, rewrite history with a safe tool such as `git filter-repo` or BFG, then force-push and notify collaborators.
