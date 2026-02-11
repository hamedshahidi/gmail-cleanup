from __future__ import annotations

from typing import Optional

from googleapiclient.discovery import Resource


def iter_message_id_pages(service: Resource, query: str, page_size: int = 500):
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


def remove_label(service: Resource, label_id: str, message_ids: list[str]) -> None:
    service.users().messages().batchModify(
        userId="me",
        body={
            "ids": message_ids,
            "addLabelIds": [],
            "removeLabelIds": [label_id],
        },
    ).execute()
