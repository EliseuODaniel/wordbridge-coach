"""Tests for card selection fallback and legacy lookup helpers."""

from app.services.card_selection_fallback_service import (
    find_any_eligible_card,
    get_card_review_state,
    get_word_by_rank,
)


def test_find_any_eligible_card_respects_language_window_and_exclusion(
    db_session, test_user, sample_cards
):
    card = find_any_eligible_card(
        db_session,
        target_language_id=test_user.target_language_id,
        target_language_code="en",
        max_rank=100,
        user_id=str(test_user.id),
        exclude_card_id=str(sample_cards["en_there"].id),
    )

    assert card is not None
    assert str(card.id) == str(sample_cards["en_book"].id)


def test_get_card_review_state_returns_state_when_present(
    db_session, test_user, user_card_states
):
    state = get_card_review_state(
        db_session,
        user_id=str(test_user.id),
        card_id=user_card_states[0].card_id,
    )

    assert state is not None
    assert str(state.user_id) == str(test_user.id)


def test_get_word_by_rank_uses_next_available_rank_and_exclusion(
    db_session, sample_words
):
    word = get_word_by_rank(
        db_session,
        rank=99,
        target_language_code="en",
        max_allowed_rank=100,
    )
    excluded = get_word_by_rank(
        db_session,
        rank=100,
        target_language_code="en",
        max_allowed_rank=100,
        excluded_word_id=sample_words["en_book"].id,
    )

    assert word is not None
    assert word.lemma == "book"
    assert excluded is None
