"""Tests for answer submission helper logic in the cards flow."""

import uuid

from app.core.time import utc_now
from app.models.user_card_state import MemoryStage
from app.schemas.card import AnswerRequest
from app.services.card_answer_service import (
    apply_sm2_result,
    build_answer_response,
    create_review_event,
    get_or_create_user_card_state,
)


def test_get_or_create_user_card_state_creates_default_row(db_session):
    user_id = str(uuid.uuid4())
    card_id = str(uuid.uuid4())

    state = get_or_create_user_card_state(db_session, user_id, card_id)

    assert state.user_id == user_id
    assert state.card_id == card_id
    assert state.status == MemoryStage.NEW
    assert state.total_reviews == 0
    assert state.correct_reviews == 0


def test_apply_sm2_result_updates_learning_state():
    class StubState:
        repetitions = 0
        easiness_factor = 2.5
        interval_days = 1
        next_review_at = utc_now()
        total_reviews = 0
        correct_reviews = 0
        status = MemoryStage.NEW

    state = StubState()
    next_review_at = utc_now()
    sm2_result = {
        "repetitions": 2,
        "easiness_factor": 2.7,
        "interval_days": 6,
        "next_review_at": next_review_at,
    }

    apply_sm2_result(state, sm2_result, is_correct=True)

    assert state.repetitions == 2
    assert state.easiness_factor == 2.7
    assert state.interval_days == 6
    assert state.next_review_at == next_review_at
    assert state.total_reviews == 1
    assert state.correct_reviews == 1
    assert state.status == MemoryStage.LEARNING


def test_create_review_event_and_response_keep_contract_fields():
    answer_data = AnswerRequest(
        answer="book",
        response_time_ms=2100,
        attempts=2,
        hints_used=1,
    )
    next_review_at = utc_now()
    sm2_result = {"easiness_factor": 2.4, "interval_days": 3, "next_review_at": next_review_at}

    review_event = create_review_event(
        user_id=str(uuid.uuid4()),
        card_id=str(uuid.uuid4()),
        sentence_id=str(uuid.uuid4()),
        quality=3,
        answer_data=answer_data,
        correct_answer="book",
        is_correct=True,
        previous_easiness=2.5,
        previous_interval=1,
        sm2_result=sm2_result,
    )
    response = build_answer_response(
        is_correct=True,
        correct_answer="book",
        sentence_full="The book is on the table.",
        quality=3,
        next_review_at=next_review_at,
    )

    assert review_event.user_answer == "book"
    assert review_event.hints_used == 1
    assert review_event.attempts == 2
    assert review_event.new_interval == 3
    assert response.correct is True
    assert response.correct_answer == "book"
    assert response.quality == 3
    assert response.next_review_at == next_review_at
