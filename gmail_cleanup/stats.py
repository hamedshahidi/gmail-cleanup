from __future__ import annotations

from collections import Counter
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional, Tuple

from googleapiclient.discovery import Resource


def _get_header(msg: dict, name: str) -> str:
    for h in msg.get("payload", {}).get("headers", []):
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "") or ""
    return ""


def iter_message_ids(service: Resource, query: str, limit: int = 500):
    """
    Yield message IDs up to limit.
    """
    token: Optional[str] = None
    yielded = 0
    while True:
        resp = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=min(500, limit - yielded) if limit else 500,
            pageToken=token,
        ).execute()
        msgs = resp.get("messages", [])
        for m in msgs:
            yield m["id"]
            yielded += 1
            if limit and yielded >= limit:
                return
        token = resp.get("nextPageToken")
        if not token or not msgs:
            return


def collect_sender_counts_and_dates(service: Resource, query: str, scan_limit: int = 500) -> tuple[Counter, Optional[str], Optional[str]]:
    """
    Returns:
      - Counter of From header
      - oldest date (string)
      - newest date (string)

    Based on first scan_limit messages.
    """
    senders = Counter()
    dates = []

    for msg_id in iter_message_ids(service, query, limit=scan_limit):
        msg = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="metadata",
            metadataHeaders=["From", "Date"],
        ).execute()

        frm = _get_header(msg, "From")
        dt = _get_header(msg, "Date")

        if frm:
            senders[frm] += 1
        if dt:
            try:
                dates.append(parsedate_to_datetime(dt))
            except Exception:
                pass

    if not dates:
        return senders, None, None

    oldest = min(dates).strftime("%Y-%m-%d %H:%M:%S %z")
    newest = max(dates).strftime("%Y-%m-%d %H:%M:%S %z")
    return senders, oldest, newest
