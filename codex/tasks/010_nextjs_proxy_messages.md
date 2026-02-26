# Task010 — Next.js Proxy for Account Messages

## Phase
Phase 4 — Gmail Message Listing (Read-Only)

## Goal

Expose a Next.js API route that proxies:

GET /api/accounts/{id}/messages

to:

GET /accounts/{id}/messages (FastAPI)

This allows:
- Browser → Next.js only
- Cookie forwarding
- Status code propagation
- No direct browser → FastAPI calls

## Requirements

- Create route file:
  apps/web/src/app/api/accounts/[id]/messages/route.ts

- Forward:
  - Cookies
  - Status codes
  - Response body
  - Content-Type header

- Must use FASTAPI_BASE_URL (default http://127.0.0.1:8000)
- No UI changes
- No business logic
- Minimal additive change
- Must not modify existing routes
- Must not modify backend

## Verification

- npm run build must succeed
- GET /api/accounts/{id}/messages must return same response as backend
