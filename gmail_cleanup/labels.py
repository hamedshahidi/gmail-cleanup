from __future__ import annotations

from typing import Optional

from googleapiclient.discovery import Resource


def get_or_create_label_id(service: Resource, label_name: str) -> str:
    """
    Return labelId for a label name, creating it if needed.
    """
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for lbl in labels:
        if lbl.get("name") == label_name:
            return lbl["id"]

    created = service.users().labels().create(
        userId="me",
        body={
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        },
    ).execute()
    return created["id"]


def apply_label_to_messages(service: Resource, label_id: str, message_ids: list[str]) -> None:
    service.users().messages().batchModify(
        userId="me",
        body={
            "ids": message_ids,
            "addLabelIds": [label_id],
            "removeLabelIds": [],
        },
    ).execute()
