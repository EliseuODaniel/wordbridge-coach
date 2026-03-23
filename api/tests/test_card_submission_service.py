"""Tests for the answer submission orchestrator."""

from types import SimpleNamespace

import pytest

from app.core.time import utc_now
from app.schemas.card import AnswerRequest
from app.services import card_submission_service


def test_submit_card_answer_orchestrates_dependencies(monkeypatch):
    calls = []
    fake_card = SimpleNamespace(
        sentence=SimpleNamespace(
            word=SimpleNamespace(text="book"),
            word_id="word-1",
            text="The ___ is on the table.",
            id="sentence-1",
        )
    )
    fake_state = SimpleNamespace()
    fake_review_event = object()
    fake_response = object()
    next_review_at = utc_now()

    monkeypatch.setattr(
        card_submission_service,
        "get_validated_card_or_404",
        lambda db, card_id: fake_card,
    )
    monkeypatch.setattr(
        card_submission_service,
        "evaluate_answer_submission",
        lambda card, answer_data: {
            "correct_answer": "book",
            "sentence_full": "The book is on the table.",
            "sentence_id": "sentence-1",
            "is_correct": True,
            "normalized_correct": "book",
            "quality": 4,
        },
    )
    monkeypatch.setattr(
        card_submission_service,
        "resolve_request_user_id",
        lambda db, user_id: "user-1",
    )
    monkeypatch.setattr(
        card_submission_service,
        "get_or_create_user_card_state",
        lambda db, user_id, card_id: fake_state,
    )
    monkeypatch.setattr(
        card_submission_service,
        "calculate_sm2_submission",
        lambda user_card_state, quality: {
            "previous_easiness": 2.5,
            "previous_interval": 1,
            "sm2_result": {"next_review_at": next_review_at},
        },
    )
    monkeypatch.setattr(
        card_submission_service,
        "create_review_event",
        lambda **kwargs: fake_review_event,
    )
    monkeypatch.setattr(
        card_submission_service,
        "apply_sm2_result",
        lambda user_card_state, sm2_result, is_correct: calls.append(("apply_sm2_result", is_correct)),
    )
    monkeypatch.setattr(
        card_submission_service,
        "apply_post_answer_updates",
        lambda db, **kwargs: calls.append(("apply_post_answer_updates", kwargs["word_id"])),
    )
    monkeypatch.setattr(
        card_submission_service,
        "build_answer_response",
        lambda **kwargs: fake_response,
    )

    class FakeDb:
        def add(self, obj):
            calls.append(("add", obj))

        def commit(self):
            calls.append(("commit",))

        def rollback(self):
            calls.append(("rollback",))

    response = card_submission_service.submit_card_answer(
        FakeDb(),
        card_id="card-1",
        answer_data=AnswerRequest(answer="book", response_time_ms=1200, attempts=1, hints_used=0),
        user_id=None,
    )

    assert response is fake_response
    assert calls == [
        ("add", fake_review_event),
        ("apply_sm2_result", True),
        ("apply_post_answer_updates", "word-1"),
        ("commit",),
    ]


def test_submit_card_answer_rolls_back_commit_errors(monkeypatch):
    fake_card = SimpleNamespace(
        sentence=SimpleNamespace(
            word=SimpleNamespace(text="book"),
            word_id="word-1",
            text="The ___ is on the table.",
            id="sentence-1",
        )
    )
    calls = []

    monkeypatch.setattr(card_submission_service, "get_validated_card_or_404", lambda db, card_id: fake_card)
    monkeypatch.setattr(
        card_submission_service,
        "evaluate_answer_submission",
        lambda card, answer_data: {
            "correct_answer": "book",
            "sentence_full": "The book is on the table.",
            "sentence_id": "sentence-1",
            "is_correct": True,
            "normalized_correct": "book",
            "quality": 4,
        },
    )
    monkeypatch.setattr(card_submission_service, "resolve_request_user_id", lambda db, user_id: "user-1")
    monkeypatch.setattr(card_submission_service, "get_or_create_user_card_state", lambda db, user_id, card_id: SimpleNamespace())
    monkeypatch.setattr(
        card_submission_service,
        "calculate_sm2_submission",
        lambda user_card_state, quality: {
            "previous_easiness": 2.5,
            "previous_interval": 1,
            "sm2_result": {"next_review_at": utc_now()},
        },
    )
    monkeypatch.setattr(card_submission_service, "create_review_event", lambda **kwargs: object())
    monkeypatch.setattr(card_submission_service, "apply_sm2_result", lambda *args, **kwargs: None)
    monkeypatch.setattr(card_submission_service, "apply_post_answer_updates", lambda *args, **kwargs: None)

    class FakeDb:
        def add(self, obj):
            pass

        def commit(self):
            raise RuntimeError("commit failed")

        def rollback(self):
            calls.append("rollback")

    with pytest.raises(RuntimeError, match="commit failed"):
        card_submission_service.submit_card_answer(
            FakeDb(),
            card_id="card-1",
            answer_data=AnswerRequest(answer="book", response_time_ms=1200, attempts=1, hints_used=0),
            user_id=None,
        )

    assert calls == ["rollback"]
