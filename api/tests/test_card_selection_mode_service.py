"""Tests for extracted card selection mode orchestration."""

from types import SimpleNamespace

from app.services.card_selection_mode_service import (
    select_next_card_lingvist,
    select_next_card_spec4,
)


class _FakeQuery:
    def __init__(self, user):
        self._user = user

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._user


class _FakeDb:
    def __init__(self, user):
        self._user = user

    def query(self, _model):
        return _FakeQuery(self._user)


def test_select_next_card_spec4_returns_new_card_first_when_policy_allows_it():
    selector = SimpleNamespace(
        db=None,
        progression_service=SimpleNamespace(
            get_or_create_user_progress=lambda user_id: 'progress',
            get_session_stats_for_today=lambda user_id: SimpleNamespace(cards_shown=0, new_cards_shown=0),
        ),
        get_due_review_words=lambda *_args, **_kwargs: [('word', 'state')],
        _should_try_new_card_spec4=lambda _new_share: True,
        _get_random_new_card=lambda *_args, **_kwargs: {'kind': 'new'},
        _get_review_card=lambda *_args, **_kwargs: {'kind': 'review'},
        _get_any_eligible_card=lambda *_args, **_kwargs: {'kind': 'fallback'},
    )

    result = select_next_card_spec4(selector, 'user-1')

    assert result == {'kind': 'new'}


def test_select_next_card_spec4_falls_back_to_review_and_then_fallback():
    selector = SimpleNamespace(
        db=None,
        progression_service=SimpleNamespace(
            get_or_create_user_progress=lambda user_id: 'progress',
            get_session_stats_for_today=lambda user_id: SimpleNamespace(cards_shown=4, new_cards_shown=1),
        ),
        get_due_review_words=lambda *_args, **_kwargs: [('word', 'state')],
        _should_try_new_card_spec4=lambda _new_share: False,
        _get_random_new_card=lambda *_args, **_kwargs: None,
        _get_review_card=lambda *_args, **_kwargs: {'kind': 'review'},
        _get_any_eligible_card=lambda *_args, **_kwargs: {'kind': 'fallback'},
    )

    result = select_next_card_spec4(selector, 'user-1')

    assert result == {'kind': 'review'}


def test_select_next_card_lingvist_prioritizes_relearn_before_other_paths():
    selector = SimpleNamespace(
        db=_FakeDb(SimpleNamespace(id='user-1')),
        user_model=object(),
        progression_service=SimpleNamespace(
            get_or_create_user_progress=lambda user_id: 'progress',
            get_session_stats_for_today=lambda user_id: SimpleNamespace(cards_shown=2, new_cards_shown=1),
        ),
        _get_due_relearn_card=lambda *_args, **_kwargs: {'kind': 'relearn'},
        _calculate_adaptive_new_share=lambda _user: 0.4,
        _count_reviews_due=lambda _user_id: 2,
        _should_try_new_card_lingvist=lambda **_kwargs: True,
        _get_random_new_card=lambda *_args, **_kwargs: {'kind': 'new'},
        get_due_review_words=lambda *_args, **_kwargs: [('word', 'state')],
        _get_review_card=lambda *_args, **_kwargs: {'kind': 'review'},
        _get_any_eligible_card=lambda *_args, **_kwargs: {'kind': 'fallback'},
    )

    result = select_next_card_lingvist(selector, 'user-1')

    assert result == {'kind': 'relearn'}
