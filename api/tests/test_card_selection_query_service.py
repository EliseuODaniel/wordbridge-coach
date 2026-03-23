"""Tests for card selection query helpers."""

import uuid

from app.core.time import utc_now
from app.models import ReviewEvent, UserFrequencyProgress
from app.models.user_card_state import MemoryStage
from app.services.card_selection_query_service import (
    count_reviews_due,
    get_due_relearn_candidate,
    get_due_review_candidates,
    get_recent_correct_word_ids,
)


def test_get_recent_correct_word_ids_excludes_incorrect_reviews(
    db_session, test_user, sample_cards
):
    card = sample_cards["en_book"]
    correct_event = ReviewEvent(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        card_id=card.id,
        sentence_id=card.sentence_id,
        quality=5,
        response_time_ms=1200,
        user_answer=card.sentence.word.text,
        correct_answer=card.sentence.word.text,
        was_correct=True,
        attempts=1,
        hints_used=0,
    )
    incorrect_event = ReviewEvent(
        id=str(uuid.uuid4()),
        user_id=test_user.id,
        card_id=sample_cards["en_there"].id,
        sentence_id=sample_cards["en_there"].sentence_id,
        quality=1,
        response_time_ms=1200,
        user_answer="wrong",
        correct_answer=sample_cards["en_there"].sentence.word.text,
        was_correct=False,
        attempts=1,
        hints_used=0,
    )
    db_session.add_all([correct_event, incorrect_event])
    db_session.commit()

    recent_word_ids = get_recent_correct_word_ids(db_session, str(test_user.id))

    assert card.sentence.word_id in recent_word_ids
    assert sample_cards["en_there"].sentence.word_id not in recent_word_ids


def test_get_due_review_candidates_respects_language_gating_and_exclusion(
    db_session, test_user, user_card_states, sample_words
):
    progress = UserFrequencyProgress(
        user_id=test_user.id,
        max_contiguous_mastered_rank=100,
        current_window_end_rank=200,
        word_goal_rank=200,
    )
    db_session.add(progress)

    for state in user_card_states:
        state.status = MemoryStage.LEARNING
        state.next_review_at = utc_now()
    db_session.commit()

    excluded_card_id = str(user_card_states[0].card_id)
    candidates = get_due_review_candidates(
        db_session,
        user_id=str(test_user.id),
        target_language_id=test_user.target_language_id,
        target_language_code="en",
        max_contiguous_mastered_rank=progress.max_contiguous_mastered_rank,
        max_count=50,
        exclude_card_id=excluded_card_id,
    )

    candidate_words = {word.lemma for word, _ in candidates}
    assert "book" in candidate_words
    assert "livre" not in candidate_words
    assert all(str(state.card_id) != excluded_card_id for _, state in candidates)


def test_relearn_and_review_count_queries_use_due_non_new_cards(
    db_session, test_user, user_card_states
):
    relearn_state = user_card_states[0]
    relearn_state.status = MemoryStage.LEARNING
    relearn_state.is_relearn = True
    relearn_state.relearn_due = utc_now()
    relearn_state.next_review_at = utc_now()

    review_state = user_card_states[1]
    review_state.status = MemoryStage.REVIEW
    review_state.next_review_at = utc_now()

    new_state = user_card_states[2]
    new_state.status = MemoryStage.NEW
    new_state.next_review_at = utc_now()
    db_session.commit()

    relearn_candidate = get_due_relearn_candidate(db_session, str(test_user.id))
    reviews_due = count_reviews_due(db_session, str(test_user.id))

    assert relearn_candidate is not None
    assert relearn_candidate[0].card_id == relearn_state.card_id
    assert reviews_due == 2
