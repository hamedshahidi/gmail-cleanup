# Task 001: Repo hygiene (no secrets) + ignore local DB

## Goal
Ensure the repository contains no credentials/tokens and won't accidentally track them in the future.

## Context
This repo is public-safe. Local secrets must live in app-data directories, not in git.

## Constraints
- Do NOT commit secrets.
- Do NOT change runtime behavior besides ignoring local-only files.
- Keep CLI working.

## Work
1) Update .gitignore to include:
   - *.db
   - *.sqlite
   - *.sqlite3
2) Ensure credentials.json and token files are not tracked.
   - If any are tracked, provide safe steps to remove from git history (do NOT execute destructive actions automatically).
3) Add / update docs:
   - docs/security.md explaining where credentials belong and what must never be committed.
4) Add templates only if needed:
   - .env.example (no secrets)

## Acceptance criteria
- No secret files tracked by git
- .gitignore covers DB files
- docs/security.md exists
