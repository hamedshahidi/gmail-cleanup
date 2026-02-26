# Gmail-Cleanup — Development Plan

This document tracks the incremental migration of the CLI-based Gmail cleanup tool into a cloud-ready web application.

It must be updated whenever:
- A task is completed
- A task number changes
- Scope evolves
- Architecture decisions change

---

# Phase 0 — Foundation & Architecture (Completed)

## Target Architecture

Next.js UI → FastAPI API → shared core → Gmail API

## Structure

- `apps/web` — Next.js App Router frontend
- `apps/api` — FastAPI backend
- `packages/core` — Shared domain logic
- `gmail_cleanup` — Existing CLI (must remain functional)

---

# Phase 1 — OAuth & Account Management (Completed)

## Task004 — FastAPI OAuth + Accounts
- Google OAuth start & callback
- Encrypted refresh token storage
- Session-based identity
- `/accounts` listing
- `DELETE /accounts/{id}`
- `/logout`

## Task005 — API Tests
- Health endpoint tests
- OAuth validation tests
- Account endpoint tests
- Encryption tests

## Task006 — Next.js Accounts UI
- `/accounts` page
- Proxy `/api/*` routes
- Cookie + redirect forwarding
- Connect / Disconnect / Logout flows

---

# Phase 2 — Security Hardening (Completed)

### Session Identity Isolation
- Removed first-user fallback
- Missing/invalid session creates new local user
- Prevented cross-user data exposure

### Strict OAuth State Enforcement
- Required session + query state
- Exact match validation
- One-time state consumption (replay protection)

### Production Session Hardening
- Introduced `APP_ENV`
- Enforced explicit `APP_SESSION_SECRET` in production
- Rejected placeholder secrets
- Secure cookie flags in production

---

# Phase 3 — Documentation & Repo Hygiene (Completed)

## Task007 — README Normalization & Documentation Alignment
- Normalize root README
- Normalize apps/api README
- Normalize apps/web README
- Document:
  - Environment variables
  - DB location & reset
  - Alembic migrations
  - Dev vs production behavior
  - OAuth setup notes
- Ensure documentation matches security hardening

---

# Phase 4 — Gmail Message Listing (Read-Only) (Completed)

## Task008 — Backend Contract (Stage A)
- Add `GET /accounts/{id}/messages`
- Enforce account ownership
- Introduce service abstraction
- Return normalized message DTO
- Add unit tests (no Google calls)

## Task009 — Gmail Integration (Stage B)
- Decrypt refresh token
- Build Gmail client via factory
- Call Gmail API
- Map Gmail payload → AccountMessage DTO
- Limit to 10 messages
- Return 400 on token issues
- Mock Gmail client in tests
- End-to-end manual verification successful

## Task010 — Next.js Proxy
- Add `/api/accounts/[id]/messages` route
- Forward cookies
- Forward status codes
- Forward response body
- Verified end-to-end

## Task011 — UI Integration (Stage C)
- Add "View Messages" button
- Fetch from `/api/accounts/{id}/messages`
- Render message list
- Loading state
- Error state

---

# Phase 5 — Quality & Confidence

## Task012 — Playwright E2E (Mode A) (Completed)
- Added Playwright setup in `apps/web`
- Added E2E tests with `/api/*` request mocking only
- Covered `/accounts` rendering
- Covered account details navigation
- Covered messages rendering
- Covered messages 404/400 error states
- Covered loading state with delayed mocked response
- No FastAPI or Google calls in E2E tests

---

# Phase 6 — Cleanup Workflow (Planned)

## Query → Label → Export → Trash via Web UI
- Preview mode before execution
- Enforce safety rules server-side
- Require explicit confirmation before trash
- Maintain recoverable trash-only policy

---

# Phase 7 — Multi-Account Enhancements (Planned)

- Improved account display
- Last sync time
- Reconnect flow
- Token health indicators

---

# Phase 8 — Deployment Readiness (Planned)

- Cloud configuration guide
- HTTPS cookie verification
- CI enforcement
- Migration workflow hardening
- Production session validation checks
