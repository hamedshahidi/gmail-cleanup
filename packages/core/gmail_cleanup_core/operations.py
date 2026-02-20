from __future__ import annotations

from gmail_cleanup.exporter import export_rows, write_csv, write_json
from gmail_cleanup.gmail import get_gmail_service
from gmail_cleanup.gmail_iter import iter_message_id_pages
from gmail_cleanup.labels import apply_label_to_messages, get_or_create_label_id
from gmail_cleanup.preview import count_messages, sample_messages
from gmail_cleanup.query_builder import QueryOptions, build_query
from gmail_cleanup.trash import trash_message_ids

from .models import (
    ExportRequest,
    ExportResult,
    LabelRequest,
    LabelResult,
    QueryRequest,
    QueryResult,
    TrashRequest,
    TrashResult,
)


def _build_query_or_raise(request: QueryRequest) -> str:
    if request.has_attachment and request.no_attachment:
        raise ValueError("Choose only one: has_attachment or no_attachment")

    opts = QueryOptions(
        q=request.q,
        from_=request.from_,
        to=request.to,
        subject=request.subject,
        has_words=request.has_words,
        not_has_words=request.not_has_words,
        label=request.label,
        in_="inbox" if request.inbox else None,
        after=request.after,
        before=request.before,
        older_than=request.older_than,
        newer_than=request.newer_than,
        has_attachment=True if request.has_attachment else (False if request.no_attachment else None),
        larger=request.larger,
        smaller=request.smaller,
    )
    built = build_query(opts)
    if not built:
        raise ValueError("Refusing to run an empty query.")
    return built


def run_query(request: QueryRequest, service=None) -> QueryResult:
    built = _build_query_or_raise(request)
    svc = service or get_gmail_service()

    total = count_messages(svc, built)
    with_att = count_messages(svc, f"{built} has:attachment")
    without_att = count_messages(svc, f"{built} -has:attachment")

    rows: list[dict] = []
    if request.sample > 0 and total > 0:
        rows = sample_messages(svc, built, limit=request.sample)

    return QueryResult(
        query=built,
        total=total,
        with_attachments=with_att,
        without_attachments=without_att,
        samples=rows,
    )


def apply_label(request: LabelRequest, service=None) -> LabelResult:
    built = _build_query_or_raise(request)
    svc = service or get_gmail_service()

    label_id = get_or_create_label_id(svc, request.target_label)
    total = count_messages(svc, built)

    done = 0
    if total > 0:
        for ids in iter_message_id_pages(svc, built, limit=request.limit):
            apply_label_to_messages(svc, label_id, ids)
            done += len(ids)

    return LabelResult(
        query=built,
        target_label=request.target_label,
        label_id=label_id,
        total_matched=total,
        labeled=done,
    )


def export_messages(request: ExportRequest, service=None) -> ExportResult:
    built = _build_query_or_raise(request)
    svc = service or get_gmail_service()

    total = count_messages(svc, built)
    export_n = min(total, request.limit)
    rows = export_rows(svc, built, limit=export_n)

    if request.out is not None:
        if request.fmt == "csv":
            write_csv(rows, request.out)
        elif request.fmt == "json":
            write_json(rows, request.out)
        else:
            raise ValueError("fmt must be csv or json")

    return ExportResult(
        query=built,
        total_matched=total,
        exported=len(rows),
        fmt=request.fmt,
        out=request.out,
    )


def trash_by_label(request: TrashRequest, service=None) -> TrashResult:
    if not request.label.startswith("cleanup/"):
        raise ValueError("For safety, label must start with 'cleanup/'.")

    svc = service or get_gmail_service()
    query = f"label:{request.label}"
    total = count_messages(svc, query)
    target_n = min(total, request.limit) if request.limit else total

    if target_n > request.max_trash_without_force and not request.force:
        raise ValueError(
            f"Refusing to trash {target_n} messages without force "
            f"(max_trash_without_force={request.max_trash_without_force})."
        )

    if not request.execute:
        return TrashResult(
            label=request.label,
            query=query,
            total_matched=total,
            target_count=target_n,
            trashed=0,
            dry_run=True,
        )

    done = 0
    for ids in iter_message_id_pages(svc, query, limit=target_n):
        trash_message_ids(svc, ids)
        done += len(ids)

    return TrashResult(
        label=request.label,
        query=query,
        total_matched=total,
        target_count=target_n,
        trashed=done,
        dry_run=False,
    )
