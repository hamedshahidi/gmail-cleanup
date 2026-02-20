from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class QueryRequest:
    q: Optional[str] = None
    from_: Optional[str] = None
    to: Optional[str] = None
    subject: Optional[str] = None
    has_words: Optional[str] = None
    not_has_words: Optional[str] = None
    label: Optional[str] = None
    inbox: bool = False
    after: Optional[str] = None
    before: Optional[str] = None
    older_than: Optional[str] = None
    newer_than: Optional[str] = None
    has_attachment: bool = False
    no_attachment: bool = False
    larger: Optional[str] = None
    smaller: Optional[str] = None
    sample: int = 10


@dataclass(frozen=True)
class QueryResult:
    query: str
    total: int
    with_attachments: int
    without_attachments: int
    samples: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class LabelRequest(QueryRequest):
    target_label: str = "cleanup/candidates"
    limit: int = 0


@dataclass(frozen=True)
class LabelResult:
    query: str
    target_label: str
    label_id: str
    total_matched: int
    labeled: int


@dataclass(frozen=True)
class ExportRequest(QueryRequest):
    out: Optional[Path] = None
    fmt: str = "csv"
    limit: int = 200


@dataclass(frozen=True)
class ExportResult:
    query: str
    total_matched: int
    exported: int
    fmt: str
    out: Optional[Path]


@dataclass(frozen=True)
class TrashRequest:
    label: str
    execute: bool = False
    limit: int = 0
    force: bool = False
    max_trash_without_force: int = 5000


@dataclass(frozen=True)
class TrashResult:
    label: str
    query: str
    total_matched: int
    target_count: int
    trashed: int
    dry_run: bool
