"""Tests for the Lingvist selection orchestration service."""

from types import SimpleNamespace

from fastapi import HTTPException
import pytest

from app.services import card_lingvist_service


def test_get_next_lingvist_card_response_restores_target_new_words(monkeypatch):
    user = SimpleNamespace(target_new_words=35)
    calls = []

    monkeypatch.setattr(card_lingvist_service, "resolve_request_user_id", lambda db, user_id: "user-1")
    monkeypatch.setattr(card_lingvist_service, "get_lingvist_user", lambda db, user_id: user)

    class FakeSelectionService:
        def __init__(self, db):
            pass

        def get_next_card_for_user(self, user_id, exclude_card_id=None):
            calls.append((user_id, exclude_card_id, user.target_new_words))
            return {"card_id": "card-1"}

    monkeypatch.setattr(card_lingvist_service, "CardSelectionService", FakeSelectionService)
    monkeypatch.setattr(
        card_lingvist_service,
        "build_lingvist_card_response",
        lambda **kwargs: {"card_id": kwargs["card_context"]["card_id"]},
    )

    class FakeDb:
        def commit(self):
            calls.append(("commit",))

    response = card_lingvist_service.get_next_lingvist_card_response(
        FakeDb(),
        user_id=None,
        exclude_card_id="card-x",
        autofill_translations=object(),
    )

    assert response == {"card_id": "card-1"}
    assert calls[0] == ("user-1", "card-x", card_lingvist_service.LINGVIST_TARGET_NEW_WORDS)
    assert calls[1] == ("commit",)
    assert user.target_new_words == 35


def test_get_next_lingvist_card_response_raises_when_selection_is_empty(monkeypatch):
    monkeypatch.setattr(card_lingvist_service, "resolve_request_user_id", lambda db, user_id: "user-1")
    monkeypatch.setattr(card_lingvist_service, "get_lingvist_user", lambda db, user_id: None)

    class FakeSelectionService:
        def __init__(self, db):
            pass

        def get_next_card_for_user(self, user_id, exclude_card_id=None):
            return None

    monkeypatch.setattr(card_lingvist_service, "CardSelectionService", FakeSelectionService)

    with pytest.raises(HTTPException) as exc_info:
        card_lingvist_service.get_next_lingvist_card_response(
            object(),
            user_id=None,
            exclude_card_id=None,
            autofill_translations=object(),
        )

    assert exc_info.value.status_code == 404


def test_get_next_lingvist_card_response_restores_target_new_words_on_selection_error(monkeypatch):
    user = SimpleNamespace(target_new_words=50)

    monkeypatch.setattr(card_lingvist_service, "resolve_request_user_id", lambda db, user_id: "user-1")
    monkeypatch.setattr(card_lingvist_service, "get_lingvist_user", lambda db, user_id: user)

    class FakeSelectionService:
        def __init__(self, db):
            pass

        def get_next_card_for_user(self, user_id, exclude_card_id=None):
            raise RuntimeError("selection failed")

    monkeypatch.setattr(card_lingvist_service, "CardSelectionService", FakeSelectionService)

    with pytest.raises(RuntimeError, match="selection failed"):
        card_lingvist_service.get_next_lingvist_card_response(
            object(),
            user_id=None,
            exclude_card_id=None,
            autofill_translations=object(),
        )

    assert user.target_new_words == 50
