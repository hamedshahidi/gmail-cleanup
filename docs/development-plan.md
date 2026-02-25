# Gmail-Cleanup — Development Plan

This document tracks the incremental migration of the CLI-based Gmail cleanup tool into a cloud-ready web application.

It is updated continuously as milestones are completed or architectural decisions evolve.

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

### Task004 — FastAPI OAuth + Accounts
- Google OAuth start & callback
- Encrypted refresh token storage
- Session-based identity
- `/accounts` listing
- `DELETE /accounts/{id}`
- `/logout`

### Task005 — API Tests
- Health endpoint tests
- OAuth start/callback validation tests
- Account endpoint tests
- Encryption tests

### Task006 — Next.js Accounts UI
- `/accounts` page
- Proxy `/api/*` routes
- Cookie + redirect forwarding
- Connect / Disconnect / Logout flows

---

# Phase 2 — Security Hardening (Completed)

### Stage 1 — Session Identity Isolation
- Removed first-user fallback
- Missing/invalid session creates new local user
- Prevents cross-user data exposure

### Stage 2 — Strict OAuth State Enforcement
- Requires session + query state
- Exact match validation
- One-time state consumption (replay protection)
- Added tests for missing/mismatch/replay

### Stage 3 — Production Session Hardening
- Introduced `APP_ENV`
- Enforced explicit `APP_SESSION_SECRET` in production
- Rejected placeholder secrets
- Secure cookie flags in production
- Added validation tests

---

# Phase 3 — Documentation & Repo Hygiene (Completed)

- Normalized README files
- Documented DB location and reset steps
- Documented environment variables
- Documented dev vs production behavior
- Public-repo safety confirmed

---

# Phase 4 — Gmail Message Listing (Read-Only)

## Task007 — Backend Contract (Stage A)
- Add `GET /accounts/{id}/messages`
- Enforce account ownership
- Introduce service abstraction
- Return normalized message DTO
- Add unit tests (no Google calls)

## Task008 — Gmail Adapter (Stage B)
- Decrypt refresh token
- Refresh access token
- Call Gmail API
- Normalize headers (Subject, From, Date)
- Mock in tests

## Task009 — UI Integration (Stage C)
- Add "View Messages" button
- Next.js proxy route
- Render message list
- Loading & error states

---

# Future Phases (Planned)

## Cleanup Workflow Integration
- Query → Label → Export → Trash via Web UI
- Enforce safety rules server-side
- Preview mode before execution

## Multi-Account Enhancements
- Improved account display
- Last sync time
- Reconnect flow

## Deployment Readiness
- Cloud configuration guide
- HTTPS cookie verification
- CI enforcement (no secrets, tests must pass)
- Alembic migration workflow

---

# Ongoing Rules

- All safety enforcement remains server-side.
- Tests must never call Google endpoints.
- CLI must remain fully functional.
- Minimal, incremental, additive changes only.
- No secrets committed.
- Update this document after every completed milestone.
