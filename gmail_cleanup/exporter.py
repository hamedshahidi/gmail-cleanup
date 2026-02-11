from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List

from googleapiclient.discovery import Resource

from gmail_cleanup.gmail_iter import iter_message_ids


def _get_headers(msg: dict) -> Dict[str, str]:
    headers = msg.get("payload", {}).get("headers", [])
    m = {h["name"].lower(): h["value"] for h in headers}
    return {
        "date": m.get("date", ""),
        "from": m.get("from", ""),
        "to": m.get("to", ""),
        "subject": m.get("subject", ""),
    }


def fetch_message_row(service: Resource, msg_id: str) -> Dict[str, str]:
    msg = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="metadata",
        metadataHeaders=["Date", "From", "To", "Subject"],
    ).execute()

    h = _get_headers(msg)
    return {"id": msg_id, **h}


def export_rows(service: Resource, query: str, limit: int = 200) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for msg_id in iter_message_ids(service, query, limit=limit):
        rows.append(fetch_message_row(service, msg_id))
    return rows


def write_csv(rows: List[Dict[str, str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "date", "from", "to", "subject"])
        w.writeheader()
        w.writerows(rows)


def write_json(rows: List[Dict[str, str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
