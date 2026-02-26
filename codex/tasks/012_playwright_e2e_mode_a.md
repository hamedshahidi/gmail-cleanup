# Task012 — Playwright E2E (Mode A: Mock /api/*)

## Phase
Phase 5 — Quality & Confidence (E2E smoke coverage)

## Goal
Add lightweight E2E coverage for the Next.js app using Playwright, with request mocking of `/api/*` so tests:
- do NOT call FastAPI
- do NOT call Google
- are stable and fast
- validate UI navigation + rendering + loading/error states

## Scope
- Install and configure Playwright in `apps/web`
- Add E2E tests that:
  1) Load `/accounts` and verify header + account row renders (mock `/api/accounts`)
  2) Navigate to account details page and verify messages render (mock `/api/accounts/{id}/messages`)
  3) Verify error state for 404/400 on messages endpoint (mocked)
  4) Verify loading state (delay mocked response)

## Requirements
- Tests MUST NOT call Google endpoints.
- Tests MUST NOT depend on FastAPI running.
- Tests MUST NOT require secrets.
- Use request interception/mocking in Playwright to return fixtures.
- Keep changes minimal and additive.
- Keep CLI untouched.

## Files / Changes
Create/Modify under `apps/web` only:
- Add Playwright config
- Add `tests/e2e/*.spec.ts` (or `e2e/*.spec.ts`) with mocked `/api` responses
- Add npm scripts:
  - `test:e2e`
  - `test:e2e:ui` (optional)
- Ensure `npm run build` still passes

## Verification
From repo root:
- `python -m pytest -q`
From `apps/web`:
- `npm install`
- `npm run build`
- `npm run test:e2e`

## Notes
- Keep mocking deterministic.
- Do not introduce any direct calls to FastAPI or Google in tests.
