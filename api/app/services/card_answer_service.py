"""Helpers for answer submission side effects in card endpoints."""

import uuid

from app.core.time import utc_now
from app.models import ReviewEvent, UserCardState
from app.models.user_card_state import MemoryStage
from app.schemas.card import AnswerRequest, AnswerResponse


def get_or_create_user_card_state(db, user_id: str, card_id: str) -> UserCardState:
    """Load the per-user card state, creating the default row when absent."""
    user_card_state = db.query(UserCardState).filter(
        UserCardState.user_id == user_id,
        UserCardState.card_id == card_id,
    ).first()

    if user_card_state:
        return user_card_state

    user_card_state = UserCardState(
        id=str(uuid.uuid4()),
        user_id=user_id,
        card_id=card_id,
        repetitions=0,
        easiness_factor=2.5,
        interval_days=1,
        next_review_at=utc_now(),
        status=MemoryStage.NEW,
        total_reviews=0,
        correct_reviews=0,
    )
    db.add(user_card_state)
    return user_card_state


def create_review_event(
    *,
    user_id: str,
    card_id: str,
    sentence_id: str,
    quality: int,
    answer_data: AnswerRequest,
    correct_answer: str,
    is_correct: bool,
    previous_easiness: float,
    previous_interval: int,
    sm2_result: dict,
) -> ReviewEvent:
    """Build the persisted review event for a submitted answer."""
    return ReviewEvent(
        user_id=user_id,
        card_id=card_id,
        sentence_id=sentence_id,
        quality=quality,
        response_time_ms=answer_data.response_time_ms,
        user_answer=answer_data.answer,
        correct_answer=correct_answer,
        was_correct=is_correct,
        hints_used=answer_data.hints_used,
        attempts=answer_data.attempts,
        previous_easiness=previous_easiness,
        new_easiness=sm2_result["easiness_factor"],
        previous_interval=previous_interval,
        new_interval=sm2_result["interval_days"],
        session_id=answer_data.session_id,
        mode=answer_data.mode,
        task_type=answer_data.task_type,
        modality="reading_writing",
        scaffold_level=(
            "independent"
            if answer_data.hints_used == 0 and answer_data.attempts == 1
            else "guided"
            if answer_data.hints_used <= 2 and answer_data.attempts <= 2
            else "high_support"
        ),
        was_independent=answer_data.hints_used == 0 and answer_data.attempts == 1,
        policy_version="pedagogy-policy-v1",
    )


def apply_sm2_result(user_card_state: UserCardState, sm2_result: dict, is_correct: bool) -> None:
    """Apply the SM-2 result back into the user-card state."""
    user_card_state.repetitions = sm2_result["repetitions"]
    user_card_state.easiness_factor = sm2_result["easiness_factor"]
    user_card_state.interval_days = sm2_result["interval_days"]
    user_card_state.next_review_at = sm2_result["next_review_at"]
    user_card_state.total_reviews += 1
    if is_correct:
        user_card_state.correct_reviews += 1

    if user_card_state.interval_days >= 21:
        user_card_state.status = MemoryStage.MATURE
    elif user_card_state.repetitions > 0:
        user_card_state.status = MemoryStage.LEARNING
    else:
        user_card_state.status = MemoryStage.NEW


def build_answer_response(
    *,
    is_correct: bool,
    correct_answer: str,
    sentence_full: str,
    quality: int,
    next_review_at,
    competency=None,
    scheduler_shadow=None,
) -> AnswerResponse:
    """Serialize the stable answer payload returned by the endpoint."""
    return AnswerResponse(
        correct=is_correct,
        correct_answer=correct_answer,
        sentence_full=sentence_full,
        quality=quality,
        next_review_at=next_review_at,
        competency=competency,
        scheduler_shadow=scheduler_shadow,
    )
