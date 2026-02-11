from __future__ import annotations

from email.utils import parsedate_to_datetime
from typing import List

from googleapiclient.discovery import Resource

from gmail_cleanup.gmail_iter import iter_message_id_pages


def count_messages(service: Resource, query: str) -> int:
    """
    Count how many messages match a Gmail query.
    """
    total = 0
    for ids in iter_message_id_pages(service, query):
        total += len(ids)
    return total


def sample_messages(service: Resource, query: str, limit: int = 10) -> List[dict]:
    """
    Return a small sample of messages with date, from, subject.
    """
    rows: List[dict] = []
    collected = 0

    for ids in iter_message_id_pages(service, query, limit=limit):
        for msg_id in ids:
            if collected >= limit:
                return rows

            msg = service.users().messages().get(
                userId="me",
                id=msg_id,
                format="metadata",
                metadataHeaders=["From", "Date", "Subject"],
            ).execute()

            headers = {
                h["name"].lower(): h.get("value", "")
                for h in msg.get("payload", {}).get("headers", [])
            }

            date_raw = headers.get("date", "")
            try:
                date_fmt = parsedate_to_datetime(date_raw).strftime(
                    "%Y-%m-%d %H:%M:%S %z"
                )
            except Exception:
                date_fmt = date_raw

            rows.append(
                {
                    "date": date_fmt,
                    "from": headers.get("from", ""),
                    "subject": headers.get("subject", ""),
                }
            )
            collected += 1

        if collected >= limit:
            break

    return rows
