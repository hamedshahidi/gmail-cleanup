# Task008 — Gmail Message Listing (Stage A)

## Phase
Phase 4 — Gmail Message Listing (Read-only)

## Goal

Introduce a read-only backend contract for listing messages
for a connected Gmail account.

This stage does NOT call Google.

## Endpoint

GET /accounts/{id}/messages

## Requirements

- Must enforce strict session ownership.
- Account must belong to current session user.
- Return 404 if:
  - Account does not exist
  - Account belongs to another user
- No Google API calls.
- Introduce service abstraction layer.
- Route handler must remain thin.
- Tests must mock the service.
- CLI must remain fully functional.
- Minimal additive changes only.

## Response Shape

[
  {
    "id": "string",
    "subject": "string",
    "from": "string",
    "snippet": "string",
    "date": "ISO datetime string"
  }
]

## Implementation Constraints

- Create service:
  apps/api/app/services/account_messages_service.py

- Create schema:
  apps/api/app/schemas/messages.py

- Modify:
  accounts route to add new endpoint.

- Add tests:
  tests/api/test_account_messages.py

- No direct Gmail imports in route.
- No token usage yet.
- Do not modify CLI.
- Output unified diff only.
