"""Orchestration for card answer submission."""

from fastapi import HTTPException, status

from app.schemas.card import AnswerRequest, AnswerResponse
from app.services.card_answer_service import (
    apply_sm2_result,
    build_answer_response,
    create_review_event,
    get_or_create_user_card_state,
)
from app.services.card_progress_service import apply_post_answer_updates
from app.services.card_response_service import resolve_request_user_id
from app.services.sm2 import SM2Algorithm
from app.services.competency_service import (
    build_card_competency_context,
    record_card_observation,
)
from app.services.content_quality_service import validate_cloze_content
from app.services.fsrs_shadow_service import apply_fsrs_shadow


def get_validated_card_or_404(db, card_id: str):
    """Load a card and ensure its required relationships are present."""
    from app.models import Card

    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Card not found", "message": f"No Card found with ID {card_id}"},
        )

    if not card.sentence:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Card data incomplete", "message": f"Card {card_id} has no sentence"},
        )

    if not card.sentence.word:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Card data incomplete",
                "message": f"Card {card_id} sentence has no word",
            },
        )

    content_validation = validate_cloze_content(card.sentence, card.sentence.word)
    if not content_validation.valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Content failed pedagogical validation",
                "issues": list(content_validation.issues),
            },
        )

    return card


def evaluate_answer_submission(card, answer_data: AnswerRequest) -> dict:
    """Validate the answer and compute the SM-2 quality payload."""
    correct_answer = card.sentence.word.text
    sentence_full = card.sentence.text.replace("___", correct_answer, 1)
    sentence_id = str(card.sentence.id)

    word_features = card.sentence.word.features if isinstance(card.sentence.word.features, dict) else {}
    accepted_answers = word_features.get("accepted_answers", [])
    is_correct, normalized_correct = SM2Algorithm.validate_answer(
        user_answer=answer_data.answer,
        correct_answer=correct_answer,
        synonyms=accepted_answers if isinstance(accepted_answers, list) else [],
    )
    quality = SM2Algorithm.calculate_quality_from_response(
        was_correct=is_correct,
        response_time_ms=answer_data.response_time_ms,
        hints_used=answer_data.hints_used,
        attempts=answer_data.attempts,
    )

    return {
        "correct_answer": correct_answer,
        "sentence_full": sentence_full,
        "sentence_id": sentence_id,
        "is_correct": is_correct,
        "normalized_correct": normalized_correct,
        "quality": quality,
    }


def calculate_sm2_submission(user_card_state, quality: int) -> dict:
    """Capture previous state and compute the next SM-2 review payload."""
    previous_easiness = user_card_state.easiness_factor
    previous_interval = user_card_state.interval_days
    sm2_result = SM2Algorithm.calculate_next_review(
        quality=quality,
        current_repetitions=user_card_state.repetitions,
        current_easiness_factor=user_card_state.easiness_factor,
        current_interval_days=user_card_state.interval_days,
    )
    return {
        "previous_easiness": previous_easiness,
        "previous_interval": previous_interval,
        "sm2_result": sm2_result,
    }


def submit_card_answer(db, *, card_id: str, answer_data: AnswerRequest, user_id=None) -> AnswerResponse:
    """Run the full answer submission workflow and return the stable API response."""
    card = get_validated_card_or_404(db, card_id)
    evaluation = evaluate_answer_submission(card, answer_data)
    resolved_user_id = resolve_request_user_id(db, user_id)
    user_card_state = get_or_create_user_card_state(db, resolved_user_id, card_id)
    sm2_payload = calculate_sm2_submission(user_card_state, evaluation["quality"])

    review_event = create_review_event(
        user_id=resolved_user_id,
        card_id=card_id,
        sentence_id=evaluation["sentence_id"],
        quality=evaluation["quality"],
        answer_data=answer_data,
        correct_answer=evaluation["correct_answer"],
        is_correct=evaluation["is_correct"],
        previous_easiness=sm2_payload["previous_easiness"],
        previous_interval=sm2_payload["previous_interval"],
        sm2_result=sm2_payload["sm2_result"],
    )
    db.add(review_event)

    scheduler_shadow = apply_fsrs_shadow(
        user_card_state,
        review_event,
        quality=evaluation["quality"],
        response_time_ms=answer_data.response_time_ms,
    )
    record_card_observation(
        db,
        user_id=resolved_user_id,
        card=card,
        answer_data=answer_data,
        was_correct=evaluation["is_correct"],
    )

    apply_sm2_result(
        user_card_state,
        sm2_payload["sm2_result"],
        evaluation["is_correct"],
    )
    apply_post_answer_updates(
        db,
        user_id=resolved_user_id,
        card_id=card_id,
        word_id=str(card.sentence.word_id),
        sentence_id=evaluation["sentence_id"],
        user_card_state=user_card_state,
        is_correct=evaluation["is_correct"],
        quality=evaluation["quality"],
        response_time_ms=answer_data.response_time_ms,
    )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    competency = build_card_competency_context(
        db,
        user_id=resolved_user_id,
        card=card,
    )

    return build_answer_response(
        is_correct=evaluation["is_correct"],
        correct_answer=evaluation["correct_answer"],
        sentence_full=evaluation["sentence_full"],
        quality=evaluation["quality"],
        next_review_at=sm2_payload["sm2_result"]["next_review_at"],
        competency=competency,
        scheduler_shadow=scheduler_shadow,
    )
