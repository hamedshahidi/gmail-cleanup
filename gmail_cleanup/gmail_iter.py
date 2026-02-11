from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional

from googleapiclient.discovery import Resource


@dataclass(frozen=True)
class IterDefaults:
    page_size: int = 500  # Gmail list maxResults cap is 500


DEFAULTS = IterDefaults()


def iter_message_id_pages(
    service: Resource,
    query: str,
    page_size: int = DEFAULTS.page_size,
    limit: int = 0,
) -> Iterator[list[str]]:
    """
    Yield pages (lists) of Gmail message IDs for a query.

    Args:
      service: Gmail API service
      query: Gmail search query
      page_size: list() page size (max 500)
      limit: max message IDs overall (0 = no limit)

    Yields:
      list[str] of message IDs
    """
    token: Optional[str] = None
    yielded = 0

    while True:
        if limit:
            remaining = limit - yielded
            if remaining <= 0:
                return
            size = min(page_size, remaining)
        else:
            size = page_size

        resp = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=size,
            pageToken=token,
        ).execute()

        msgs = resp.get("messages", [])
        ids = [m["id"] for m in msgs]

        if ids:
            yield ids
            yielded += len(ids)

        token = resp.get("nextPageToken")
        if not token or not msgs:
            return


def iter_message_ids(
    service: Resource,
    query: str,
    page_size: int = DEFAULTS.page_size,
    limit: int = 0,
) -> Iterator[str]:
    """
    Flattened iterator that yields message IDs one by one.
    """
    for page in iter_message_id_pages(service, query, page_size=page_size, limit=limit):
        for mid in page:
            yield mid
