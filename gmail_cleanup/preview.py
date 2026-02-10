from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from googleapiclient.discovery import Resource


BATCH_SIZE = 500


def count_messages(service: Resource, query: str) -> int:
    total = 0
    token: Optional[str] = None
    while True:
        resp = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=BATCH_SIZE,
            pageToken=token,
        ).execute()
        total += len(resp.get("messages", []))
        token = resp.get("nextPageToken")
        if not token:
            break
    return total


def sample_messages(service: Resource, query: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Returns list of {date, from, subject} for first N messages.
    """
    resp = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=min(limit, 50),
    ).execute()

    msgs = resp.get("messages", [])
    if not msgs:
        return []

    out: List[Dict[str, str]] = []
    for m in msgs[:limit]:
        msg = service.users().messages().get(
            userId="me",
            id=m["id"],
            format="metadata",
            metadataHeaders=["Date", "From", "Subject"],
        ).execute()

        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        out.append(
            {
                "date": headers.get("date", ""),
                "from": headers.get("from", ""),
                "subject": headers.get("subject", ""),
            }
        )

    return out
