# Task009 — Gmail Message Listing (Stage B)

## Phase
Phase 4 — Gmail Message Listing (Read-only)

## Goal

Integrate real Gmail API message listing into AccountMessagesService.

Stage A contract remains unchanged.

## Requirements

- Must enforce account ownership.
- Must decrypt refresh token using existing encryption system.
- Must introduce GmailClientFactory abstraction.
- Must return maximum 10 messages.
- Must map Gmail API payload to AccountMessage DTO.
- Must return ISO datetime.
- Must return 400 if:
  - Refresh token missing
  - Token decryption fails
  - Gmail authentication fails
- Must return 404 if:
  - Account does not exist
  - Account not owned
- Must not modify CLI.
- Must not call Google in tests.
- Must preserve dependency injection patterns.
- Minimal additive changes only.

## Files To Create

- apps/api/app/services/gmail_client.py
- tests/api/test_account_messages_service.py

## Files To Modify

- apps/api/app/services/account_messages_service.py
- apps/api/app/main.py (dependency injection updates only)

## Testing Constraints

- GmailClientFactory must be injectable.
- Tests must mock GmailClientFactory.
- No real Google API calls.
- No real credentials usage.

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
