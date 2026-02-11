from __future__ import annotations

from googleapiclient.discovery import Resource

from gmail_cleanup.gmail_iter import iter_message_id_pages


def trash_message_ids(service: Resource, ids: list[str]) -> None:
    """
    Move a batch of messages to Trash (recoverable).
    """
    service.users().messages().batchModify(
        userId="me",
        body={"ids": ids, "addLabelIds": ["TRASH"], "removeLabelIds": []},
    ).execute()


def trash_query(service: Resource, query: str, limit: int = 0) -> int:
    """
    Trash messages matching query. Returns how many were trashed.
    """
    done = 0
    for ids in iter_message_id_pages(service, query, limit=limit):
        if not ids:
            break
        trash_message_ids(service, ids)
        done += len(ids)
        if limit and done >= limit:
            break
    return done
