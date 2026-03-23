"""Tests for card selection policy helpers."""

from app.services.card_selection_policy_service import (
    calculate_adaptive_new_share,
    calculate_session_new_share,
    should_try_new_card_lingvist,
    should_try_new_card_spec4,
)


def test_calculate_session_new_share_handles_zero_cards():
    assert calculate_session_new_share(0, 0) == 0.0
    assert calculate_session_new_share(8, 2) == 0.25


def test_spec4_policy_tries_new_only_below_target_share():
    assert should_try_new_card_spec4(0.10) is True
    assert should_try_new_card_spec4(0.25) is False


def test_lingvist_adaptive_share_respects_backlog_and_accuracy():
    assert calculate_adaptive_new_share(0.95, 10) == 0.25
    assert calculate_adaptive_new_share(0.65, 10) == 0.10
    assert calculate_adaptive_new_share(None, 10) == 0.15
    assert calculate_adaptive_new_share(0.95, 51) == 0.0


def test_lingvist_policy_requires_capacity_and_backlog_room():
    assert should_try_new_card_lingvist(
        current_new_share=0.05,
        adaptive_new_share=0.15,
        reviews_due_count=10,
    ) is True
    assert should_try_new_card_lingvist(
        current_new_share=0.15,
        adaptive_new_share=0.15,
        reviews_due_count=10,
    ) is False
    assert should_try_new_card_lingvist(
        current_new_share=0.05,
        adaptive_new_share=0.15,
        reviews_due_count=60,
    ) is False
