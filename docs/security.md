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

## If a secret was committed

1. Revoke or rotate the leaked credential immediately in the provider console.
2. Remove the file from tracking:
   - `git rm --cached <path-to-secret>`
   - `git commit -m "stop tracking secret file"`
3. If already pushed, rewrite history with a safe tool such as `git filter-repo` or BFG, then force-push and notify collaborators.

