# Architecture

## Target architecture

The target structure is:

`Next.js UI -> FastAPI API -> shared core -> Gmail API`

## Layers

- `apps/web` (Next.js UI):
  - User-facing workflow for query, label, export, and trash.
  - Talks only to HTTP endpoints in `apps/api`.

- `apps/api` (FastAPI):
  - Request validation, auth/session boundary, and endpoint orchestration.
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