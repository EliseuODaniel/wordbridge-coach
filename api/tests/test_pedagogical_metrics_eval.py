"""Deterministic regression checks for cross-mode pedagogical signals."""

import pytest

from app.services.chat_profile_service import derive_pedagogical_metrics
from app.services.lingvist_difficulty_service import get_lingvist_difficulty_profile


@pytest.mark.parametrize(
    ("raw_signals", "expected"),
    [
        (
            {
                "daily_new_limit": 10,
                "accuracy_last_20": 0.52,
                "average_retention": 0.48,
                "due_review_count": 34,
                "relearn_queue_count": 7,
                "difficult_card_count": 8,
                "mature_ratio": 0.08,
                "hint_ratio": 0.6,
                "average_attempts": 2.1,
                "cards_seen_today": 18,
                "session_new_ratio": 0.05,
                "preferred_mode": "spec4",
            },
            {
                "retention_band": "fragile",
                "review_pressure": "high",
                "difficulty_signal": "support_needed",
                "recommended_pace": "stabilize",
                "recommended_mode": "lingvist",
                "cefr_readiness": "solidify_current_band",
            },
        ),
        (
            {
                "daily_new_limit": 10,
                "accuracy_last_20": 0.91,
                "average_retention": 0.9,
                "due_review_count": 2,
                "relearn_queue_count": 0,
                "difficult_card_count": 0,
                "mature_ratio": 0.72,
                "hint_ratio": 0.05,
                "average_attempts": 1.0,
                "cards_seen_today": 12,
                "session_new_ratio": 0.35,
                "preferred_mode": "lingvist",
            },
            {
                "retention_band": "stable",
                "review_pressure": "low",
                "difficulty_signal": "ready_to_push",
                "recommended_pace": "accelerate",
                "recommended_mode": "chat",
                "cefr_readiness": "ready_to_probe_next_band",
            },
        ),
        (
            {
                "daily_new_limit": 10,
                "accuracy_last_20": 0.74,
                "average_retention": 0.7,
                "due_review_count": 6,
                "relearn_queue_count": 1,
                "difficult_card_count": 2,
                "mature_ratio": 0.34,
                "hint_ratio": 0.2,
                "average_attempts": 1.3,
                "cards_seen_today": 8,
                "session_new_ratio": 0.25,
                "preferred_mode": "spec4",
            },
            {
                "retention_band": "building",
                "review_pressure": "low",
                "difficulty_signal": "on_target",
                "recommended_pace": "balance",
                "recommended_mode": "spec4",
                "cefr_readiness": "operating_at_band",
            },
        ),
    ],
)
def test_pedagogical_metrics_match_expected_learning_policy(raw_signals, expected):
    """Pedagogical policy outputs should stay stable for representative learners."""
    metrics = derive_pedagogical_metrics(**raw_signals)

    for key, value in expected.items():
        assert metrics[key] == value


def test_unknown_retention_does_not_accelerate_new_or_unobserved_profiles():
    """A profile with no accuracy or retention evidence should stay in balance."""
    metrics = derive_pedagogical_metrics(
        daily_new_limit=10,
        accuracy_last_20=None,
        average_retention=None,
        due_review_count=0,
        relearn_queue_count=0,
        difficult_card_count=0,
        mature_ratio=None,
        hint_ratio=None,
        average_attempts=None,
        cards_seen_today=0,
        session_new_ratio=None,
        preferred_mode="spec4",
    )

    assert metrics["retention_band"] == "unknown"
    assert metrics["difficulty_signal"] == "on_target"
    assert metrics["recommended_pace"] == "balance"
    assert metrics["recommended_mode"] == "spec4"


def test_lingvist_profile_uses_metrics_to_adjust_sentence_difficulty():
    """The same learner phase should adapt based on support or stretch signals."""
    support_profile = get_lingvist_difficulty_profile(
        max_contiguous_mastered_rank=900,
        current_window_end_rank=1000,
        recent_accuracy=0.52,
        review_pressure="high",
        difficulty_signal="support_needed",
    )
    stretch_profile = get_lingvist_difficulty_profile(
        max_contiguous_mastered_rank=900,
        current_window_end_rank=1000,
        recent_accuracy=0.91,
        review_pressure="low",
        difficulty_signal="ready_to_push",
    )

    assert support_profile.pace_hint == "stabilize"
    assert support_profile.target_sentence_difficulty < stretch_profile.target_sentence_difficulty
    assert support_profile.ranked_candidate_pool < stretch_profile.ranked_candidate_pool
    assert stretch_profile.pace_hint == "accelerate"


@pytest.mark.parametrize(
    ("simulated_user", "expected"),
    [
        (
            {
                "name": "fragile expanding learner",
                "max_contiguous_mastered_rank": 900,
                "current_window_end_rank": 1000,
                "recent_accuracy": 0.52,
                "review_pressure": "high",
                "difficulty_signal": "support_needed",
            },
            {
                "pace_hint": "stabilize",
                "support_bias": "support_needed",
                "target_delta": -1,
                "pool_delta": -2,
            },
        ),
        (
            {
                "name": "balanced expanding learner",
                "max_contiguous_mastered_rank": 900,
                "current_window_end_rank": 1000,
                "recent_accuracy": 0.74,
                "review_pressure": "low",
                "difficulty_signal": "on_target",
            },
            {
                "pace_hint": "balance",
                "support_bias": "on_target",
                "target_delta": 0,
                "pool_delta": 0,
            },
        ),
        (
            {
                "name": "stable expanding learner",
                "max_contiguous_mastered_rank": 900,
                "current_window_end_rank": 1000,
                "recent_accuracy": 0.91,
                "review_pressure": "low",
                "difficulty_signal": "ready_to_push",
            },
            {
                "pace_hint": "accelerate",
                "support_bias": "ready_to_push",
                "target_delta": 1,
                "pool_delta": 2,
            },
        ),
        (
            {
                "name": "high-performing learner blocked by reviews",
                "max_contiguous_mastered_rank": 900,
                "current_window_end_rank": 1000,
                "recent_accuracy": 0.91,
                "review_pressure": "high",
                "difficulty_signal": "ready_to_push",
            },
            {
                "pace_hint": "stabilize",
                "support_bias": "support_needed",
                "target_delta": -1,
                "pool_delta": -2,
            },
        ),
    ],
)
def test_lingvist_adaptation_stays_predictable_for_simulated_users(simulated_user, expected):
    """Adaptive Lingvist tuning should move one controlled step from the phase baseline."""
    baseline = get_lingvist_difficulty_profile(
        max_contiguous_mastered_rank=simulated_user["max_contiguous_mastered_rank"],
        current_window_end_rank=simulated_user["current_window_end_rank"],
    )
    adaptive = get_lingvist_difficulty_profile(
        max_contiguous_mastered_rank=simulated_user["max_contiguous_mastered_rank"],
        current_window_end_rank=simulated_user["current_window_end_rank"],
        recent_accuracy=simulated_user["recent_accuracy"],
        review_pressure=simulated_user["review_pressure"],
        difficulty_signal=simulated_user["difficulty_signal"],
    )

    assert adaptive.phase == baseline.phase
    assert adaptive.rank_limit == baseline.rank_limit
    assert adaptive.pace_hint == expected["pace_hint"]
    assert adaptive.support_bias == expected["support_bias"]
    assert adaptive.target_sentence_difficulty - baseline.target_sentence_difficulty == expected["target_delta"]
    assert adaptive.ranked_candidate_pool - baseline.ranked_candidate_pool == expected["pool_delta"]
    assert abs(adaptive.max_word_count - baseline.max_word_count) <= 2
    assert 1 <= adaptive.sentence_difficulty_min <= adaptive.target_sentence_difficulty
    assert adaptive.target_sentence_difficulty <= adaptive.sentence_difficulty_max <= 5
