from __future__ import annotations

from typing import Optional

from googleapiclient.discovery import Resource

BATCH_SIZE = 500


def iter_message_id_pages(service: Resource, query: str, page_size: int = BATCH_SIZE):
    token: Optional[str] = None
    while True:
        resp = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=page_size,
            pageToken=token,
        ).execute()
        msgs = resp.get("messages", [])
        ids = [m["id"] for m in msgs]
        if ids:
            yield ids
        token = resp.get("nextPageToken")
        if not token:
            break


def trash_message_ids(service: Resource, ids: list[str]) -> None:
    # Move to Trash (recoverable)
    service.users().messages().batchModify(
        userId="me",
        body={"ids": ids, "addLabelIds": ["TRASH"], "removeLabelIds": []},
    ).execute()
