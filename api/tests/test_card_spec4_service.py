"""Tests for the Spec4 selection response service."""

from fastapi import HTTPException
import pytest

from app.services import card_spec4_service


def test_build_spec4_card_response_keeps_contract(monkeypatch):
    monkeypatch.setattr(card_spec4_service, "get_card_memory_stage", lambda db, user_id, card_id: "LEARNING")
    monkeypatch.setattr(
        card_spec4_service,
        "load_cross_mode_learning_context",
        lambda db, user_id, mode: {
            "mode": mode,
            "cefr_level": "A2",
            "support_level": "guided_practice",
            "current_focus": "Use past simple after yesterday",
            "session_goal": "stabilize past-time verbs in short personal sentences",
            "topic": "travel",
            "feedback_language": "Portuguese",
            "why_this_now": "Recognition practice to reinforce the current focus before freer production.",
        },
    )
    card_context = {
        "card_id": "card-1",
        "word_id": "word-1",
        "sentence_id": "sentence-1",
        "word": "book",
        "sentence": "The ___ is on the table.",
        "gap": {"start": 4, "end": 7},
        "sentence_translation": "O livro está na mesa.",
        "grammar_hint": "Use the noun for something you read",
        "is_new": False,
        "audio_word_url": "/api/tts/word/card-1?text=book&lang=en",
        "audio_sentence_url": "/api/tts/sentence/card-1?text=The book is on the table.&lang=en",
        "sentence_source": "Corpus",
    }

    response = card_spec4_service.build_spec4_card_response(object(), "user-1", card_context)

    assert response.card_id == "card-1"
    assert response.memory_stage == "LEARNING"
    assert response.is_new is False
    assert response.sentence_source == "Corpus"
    assert response.learning_context.current_focus == "Use past simple after yesterday"


def test_get_next_spec4_card_response_raises_when_selection_is_empty(monkeypatch):
    monkeypatch.setattr(card_spec4_service, "resolve_request_user_id", lambda db, user_id: "user-1")

    class FakeSelectionService:
        def __init__(self, db):
            pass

        def get_next_card_for_user(self, user_id, exclude_card_id=None):
            return None

    monkeypatch.setattr(card_spec4_service, "CardSelectionService", FakeSelectionService)

    with pytest.raises(HTTPException) as exc_info:
        card_spec4_service.get_next_spec4_card_response(object(), user_id=None)

    assert exc_info.value.status_code == 404


def test_get_next_spec4_card_response_delegates_selection(monkeypatch):
    calls = []
    card_context = {
        "card_id": "card-1",
        "word_id": "word-1",
        "sentence_id": "sentence-1",
        "word": "book",
        "sentence": "The ___ is on the table.",
        "gap": {"start": 4, "end": 7},
        "sentence_translation": "O livro está na mesa.",
        "grammar_hint": "hint",
        "is_new": True,
        "audio_word_url": "word-url",
        "audio_sentence_url": "sentence-url",
    }

    monkeypatch.setattr(card_spec4_service, "resolve_request_user_id", lambda db, user_id: "user-1")

    class FakeSelectionService:
        def __init__(self, db):
            pass

        def get_next_card_for_user(self, user_id, exclude_card_id=None):
            calls.append((user_id, exclude_card_id))
            return card_context

    monkeypatch.setattr(card_spec4_service, "CardSelectionService", FakeSelectionService)
    monkeypatch.setattr(
        card_spec4_service,
        "build_spec4_card_response",
        lambda db, user_id, context: {"user_id": user_id, "card_id": context["card_id"]},
    )

    response = card_spec4_service.get_next_spec4_card_response(
        object(),
        user_id=None,
        exclude_card_id="card-x",
    )

    assert calls == [("user-1", "card-x")]
    assert response == {"user_id": "user-1", "card_id": "card-1"}
