# Task011 — Account Messages UI (Stage C)

## Phase
Phase 4 — Gmail Message Listing (Read-Only)

## Goal

Create a dedicated account details page:

/accounts/{id}

This page must:

- Fetch messages from:
  /api/accounts/{id}/messages
- Render message list
- Show:
  - Subject
  - From
  - Date
  - Snippet
- Handle loading state
- Handle error state
- Not call FastAPI directly
- Use Next.js proxy only
- Make minimal additive changes
- Not modify backend

## Files To Create

- apps/web/src/app/accounts/[id]/page.tsx

## Files To Modify

- apps/web/src/app/accounts/page.tsx
  (add link to account details page)

## Constraints

- Must use fetch to /api/accounts/{id}/messages
- Must handle 400/404 gracefully
- Must not break existing UI
- Must compile with npm run build
