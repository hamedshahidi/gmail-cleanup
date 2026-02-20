# Architecture

## Target architecture

The target structure is:

`Next.js UI -> FastAPI API -> shared core -> Gmail API`

## Layers

- `apps/web` (Next.js UI):
  - User-facing workflow for query, label, export, and trash.
  - Browser talks only to Next.js `/api/*` routes.
  - Next.js route handlers proxy requests to `apps/api`, forwarding cookies and `Set-Cookie`.

- `apps/api` (FastAPI):
  - Request validation, auth/session boundary, and endpoint orchestration.
  - Uses `SessionMiddleware` for session state.
  - Enforces strict OAuth callback state validation (required match + one-time consumption).
  - Encrypts Google refresh tokens before storing them.
  - Invokes domain operations from `packages/core`.

- `packages/core` (shared core):
  - Gmail cleanup use-cases and reusable business rules.
  - Designed to be framework-agnostic and reusable by CLI/API.

- `gmail_cleanup` (existing modules):
  - Current implementation that already talks to Gmail API.
  - Acts as the integration base while logic is incrementally extracted into `packages/core`.

## Migration intent

This scaffold is additive and non-breaking.
The existing CLI entry point remains unchanged:

`gmail-cleanup = gmail_cleanup.cli:app`

## Key auth/account flow

1. `apps/web` calls FastAPI through proxy routes only.
2. FastAPI `/oauth/google/start` saves `oauth_state` in session.
3. FastAPI `/oauth/google/callback` requires matching `state`, consumes it once, exchanges code, and stores encrypted refresh token.
4. Account APIs (`/accounts`, `DELETE /accounts/{id}`, `/logout`) are scoped by current session user.
