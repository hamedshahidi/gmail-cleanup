from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class QueryOptions:
    q: Optional[str] = None
    from_: Optional[str] = None
    to: Optional[str] = None
    subject: Optional[str] = None
    has_words: Optional[str] = None
    not_has_words: Optional[str] = None
    label: Optional[str] = None
    in_: Optional[str] = None  # inbox, any, trash, spam, etc.
    after: Optional[str] = None   # YYYY/MM/DD
    before: Optional[str] = None  # YYYY/MM/DD
    older_than: Optional[str] = None  # e.g. 30d, 12m, 2y
    newer_than: Optional[str] = None  # e.g. 7d
    has_attachment: Optional[bool] = None  # True/False/None
    larger: Optional[str] = None  # e.g. 10M
    smaller: Optional[str] = None # e.g. 2M


def build_query(opts: QueryOptions) -> str:
    parts: list[str] = []

    if opts.q:
        parts.append(opts.q)

    if opts.from_:
        parts.append(f"from:{opts.from_}")
    if opts.to:
        parts.append(f"to:{opts.to}")
    if opts.subject:
        parts.append(f"subject:{_quote_if_needed(opts.subject)}")
    if opts.label:
        parts.append(f"label:{opts.label}")
    if opts.in_:
        parts.append(f"in:{opts.in_}")

    if opts.after:
        parts.append(f"after:{opts.after}")
    if opts.before:
        parts.append(f"before:{opts.before}")
    if opts.older_than:
        parts.append(f"older_than:{opts.older_than}")
    if opts.newer_than:
        parts.append(f"newer_than:{opts.newer_than}")

    if opts.has_words:
        parts.append(_quote_if_needed(opts.has_words))
    if opts.not_has_words:
        parts.append(f"-{_quote_if_needed(opts.not_has_words)}")

    if opts.has_attachment is True:
        parts.append("has:attachment")
    elif opts.has_attachment is False:
        parts.append("-has:attachment")

    if opts.larger:
        parts.append(f"larger:{opts.larger}")
    if opts.smaller:
        parts.append(f"smaller:{opts.smaller}")

    return " ".join(parts).strip()


def _quote_if_needed(text: str) -> str:
    text = text.strip()
    if " " in text and not (text.startswith('"') and text.endswith('"')):
        return f'"{text}"'
    return text
