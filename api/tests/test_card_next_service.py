"""Tests for the legacy `/cards/next` orchestration service."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.user_card_state import MemoryStage
from app.services import card_next_service


def test_get_next_card_response_prefers_due_card(monkeypatch):
    calls = []
    due_state = SimpleNamespace(card="due-card", status=MemoryStage.LEARNING)

    monkeypatch.setattr(card_next_service, "create_sample_data_if_needed", lambda db: calls.append("bootstrap"))
    monkeypatch.setattr(card_next_service, "resolve_request_user_id", lambda db, user_id: "user-1")
    monkeypatch.setattr(
        card_next_service,
        "get_card_user_or_404",
        lambda db, user_id: SimpleNamespace(daily_new_limit=10),
    )
    monkeypatch.setattr(card_next_service, "get_due_card_state", lambda db, user_id: due_state)
    monkeypatch.setattr(
        card_next_service,
        "format_card_response",
        lambda card, status: {"card": card, "status": status.value},
    )

    response = card_next_service.get_next_card_response(object(), user_id=None)

    assert response == {"card": "due-card", "status": "LEARNING"}
    assert calls == ["bootstrap"]


def test_get_next_card_response_uses_new_card_within_daily_limit(monkeypatch):
    monkeypatch.setattr(card_next_service, "create_sample_data_if_needed", lambda db: None)
    monkeypatch.setattr(card_next_service, "resolve_request_user_id", lambda db, user_id: "user-1")
    monkeypatch.setattr(
        card_next_service,
        "get_card_user_or_404",
        lambda db, user_id: SimpleNamespace(daily_new_limit=10),
    )
    monkeypatch.setattr(card_next_service, "get_due_card_state", lambda db, user_id: None)
    monkeypatch.setattr(card_next_service, "count_new_cards_today", lambda db, user_id: 2)
    monkeypatch.setattr(
        card_next_service,
        "get_new_card_state",
        lambda db, user_id: SimpleNamespace(card="new-card", status=MemoryStage.NEW),
    )
    monkeypatch.setattr(
        card_next_service,
        "format_card_response",
        lambda card, status: {"card": card, "status": status.value},
    )

    response = card_next_service.get_next_card_response(object(), user_id=None)

    assert response == {"card": "new-card", "status": "NEW"}


def test_get_next_card_response_uses_learning_card_when_new_limit_reached(monkeypatch):
    monkeypatch.setattr(card_next_service, "create_sample_data_if_needed", lambda db: None)
    monkeypatch.setattr(card_next_service, "resolve_request_user_id", lambda db, user_id: "user-1")
    monkeypatch.setattr(
        card_next_service,
        "get_card_user_or_404",
        lambda db, user_id: SimpleNamespace(daily_new_limit=1),
    )
    monkeypatch.setattr(card_next_service, "get_due_card_state", lambda db, user_id: None)
    monkeypatch.setattr(card_next_service, "count_new_cards_today", lambda db, user_id: 1)
    monkeypatch.setattr(
        card_next_service,
        "get_learning_card_state",
        lambda db, user_id: SimpleNamespace(card="learning-card", status=MemoryStage.LEARNING),
    )
    monkeypatch.setattr(
        card_next_service,
        "format_card_response",
        lambda card, status: {"card": card, "status": status.value},
    )

    response = card_next_service.get_next_card_response(object(), user_id=None)

    assert response == {"card": "learning-card", "status": "LEARNING"}


def test_get_next_card_response_raises_when_no_card_is_available(monkeypatch):
    monkeypatch.setattr(card_next_service, "create_sample_data_if_needed", lambda db: None)
    monkeypatch.setattr(card_next_service, "resolve_request_user_id", lambda db, user_id: "user-1")
    monkeypatch.setattr(
        card_next_service,
        "get_card_user_or_404",
        lambda db, user_id: SimpleNamespace(daily_new_limit=1),
    )
    monkeypatch.setattr(card_next_service, "get_due_card_state", lambda db, user_id: None)
    monkeypatch.setattr(card_next_service, "count_new_cards_today", lambda db, user_id: 1)
    monkeypatch.setattr(card_next_service, "get_learning_card_state", lambda db, user_id: None)

    with pytest.raises(HTTPException) as exc_info:
        card_next_service.get_next_card_response(object(), user_id=None)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["error"] == "No cards available"
