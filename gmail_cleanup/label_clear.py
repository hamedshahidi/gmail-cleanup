from __future__ import annotations

from typing import List

from googleapiclient.discovery import Resource

from gmail_cleanup.gmail_iter import iter_message_id_pages


def remove_label(service: Resource, label_id: str, message_ids: List[str]) -> None:
    """
    Remove a Gmail label from a batch of messages.
    """
    service.users().messages().batchModify(
        userId="me",
        body={
            "ids": message_ids,
            "addLabelIds": [],
            "removeLabelIds": [label_id],
        },
    ).execute()


def clear_label_from_query(service: Resource, query: str, label_id: str, limit: int = 0) -> int:
    """
    Remove a label from messages matching a query.

    Args:
        service: Gmail API service
        query: Gmail search query (e.g. 'label:cleanup/test')
        label_id: Gmail label ID to remove
        limit: Max messages to update (0 = no limit)

    Returns:
        Number of messages updated
    """
    done = 0

    for ids in iter_message_id_pages(service, query, limit=limit):
        if not ids:
            break

        remove_label(service, label_id, ids)
        done += len(ids)

        if limit and done >= limit:
            break

    return done
