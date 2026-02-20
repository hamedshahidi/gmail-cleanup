from __future__ import annotations

from unittest.mock import Mock

import pytest

from gmail_cleanup_core.models import QueryRequest, TrashRequest
from gmail_cleanup_core.operations import run_query, trash_by_label


def test_run_query_refuses_empty_query(monkeypatch: pytest.MonkeyPatch) -> None:
    get_service = Mock(side_effect=AssertionError("should not call Gmail service"))
    monkeypatch.setattr("gmail_cleanup_core.operations.get_gmail_service", get_service)

    with pytest.raises(ValueError, match="empty query"):
        run_query(QueryRequest())

    get_service.assert_not_called()


def test_trash_requires_cleanup_prefix() -> None:
    with pytest.raises(ValueError, match="cleanup/"):
        trash_by_label(TrashRequest(label="inbox", execute=True))


def test_trash_dry_run_does_not_trash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("gmail_cleanup_core.operations.count_messages", lambda _svc, _q: 3)

    iter_pages = Mock(side_effect=AssertionError("should not iterate in dry-run"))
    trash_ids = Mock(side_effect=AssertionError("should not trash in dry-run"))
    monkeypatch.setattr("gmail_cleanup_core.operations.iter_message_id_pages", iter_pages)
    monkeypatch.setattr("gmail_cleanup_core.operations.trash_message_ids", trash_ids)

    result = trash_by_label(TrashRequest(label="cleanup/candidates", execute=False), service=object())
    assert result.dry_run is True
    assert result.trashed == 0
    assert result.target_count == 3


def test_trash_enforces_max_without_force(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("gmail_cleanup_core.operations.count_messages", lambda _svc, _q: 25)

    with pytest.raises(ValueError, match="without force"):
        trash_by_label(
            TrashRequest(
                label="cleanup/candidates",
                execute=True,
                max_trash_without_force=10,
            ),
            service=object(),
        )


def test_trash_force_allows_over_max(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("gmail_cleanup_core.operations.count_messages", lambda _svc, _q: 25)
    monkeypatch.setattr(
        "gmail_cleanup_core.operations.iter_message_id_pages",
        lambda _svc, _query, limit=0: [["a"] * limit] if limit else [],
    )
    trash_ids = Mock()
    monkeypatch.setattr("gmail_cleanup_core.operations.trash_message_ids", trash_ids)

    result = trash_by_label(
        TrashRequest(
            label="cleanup/candidates",
            execute=True,
            force=True,
            max_trash_without_force=10,
            limit=5,
        ),
        service=object(),
    )

    assert result.trashed == 5
    assert result.target_count == 5
    trash_ids.assert_called_once()


def test_trash_execute_calls_batch_trash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("gmail_cleanup_core.operations.count_messages", lambda _svc, _q: 3)
    monkeypatch.setattr(
        "gmail_cleanup_core.operations.iter_message_id_pages",
        lambda _svc, _query, limit=0: [["a", "b"], ["c"]],
    )
    trash_ids = Mock()
    monkeypatch.setattr("gmail_cleanup_core.operations.trash_message_ids", trash_ids)

    result = trash_by_label(
        TrashRequest(label="cleanup/candidates", execute=True),
        service=object(),
    )

    assert result.dry_run is False
    assert result.trashed == 3
    assert result.target_count == 3
    assert trash_ids.call_count == 2


def test_trash_execute_respects_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("gmail_cleanup_core.operations.count_messages", lambda _svc, _q: 100)

    captured = {}

    def _iter_pages(_svc, _query, limit=0):
        captured["svc"] = _svc
        captured["query"] = _query
        captured["limit"] = limit
        return iter([["a", "b"], ["c", "d"]])

    monkeypatch.setattr("gmail_cleanup_core.operations.iter_message_id_pages", _iter_pages)

    trash_ids = Mock()
    monkeypatch.setattr("gmail_cleanup_core.operations.trash_message_ids", trash_ids)

    service = object()
    result = trash_by_label(
        TrashRequest(label="cleanup/candidates", execute=True, limit=4),
        service=service,
    )

    assert result.target_count == 4
    assert result.trashed == 4
    assert captured["svc"] is service
    assert captured["query"] == "label:cleanup/candidates"
    assert captured["limit"] == 4
    assert trash_ids.call_count == 2
