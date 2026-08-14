"""Official FSRS 6 integration operated strictly in shadow mode."""

from __future__ import annotations

from datetime import timezone
import json

from fsrs import Card, Rating, Scheduler

from app.core.time import utc_now


FSRS_SHADOW_VERSION = "py-fsrs-6.3.0-defaults"


def quality_to_rating(quality: int) -> Rating:
    if quality <= 2:
        return Rating.Again
    if quality == 3:
        return Rating.Hard
    if quality == 4:
        return Rating.Good
    return Rating.Easy


def apply_fsrs_shadow(user_card_state, review_event, *, quality: int, response_time_ms: int, reviewed_at=None) -> dict:
    """Update FSRS telemetry without changing the production due date."""
    scheduler = Scheduler(enable_fuzzing=False)
    observed_at = reviewed_at or utc_now()
    if observed_at.tzinfo is None:
        now = observed_at.replace(tzinfo=timezone.utc)
    else:
        now = observed_at.astimezone(timezone.utc)
    now_naive = now.replace(tzinfo=None)
    if user_card_state.fsrs_card_json:
        card = Card.from_json(json.dumps(user_card_state.fsrs_card_json))
        predicted_recall = scheduler.get_card_retrievability(card, now)
    else:
        card = Card()
        predicted_recall = None
    card, review_log = scheduler.review_card(
        card,
        quality_to_rating(quality),
        review_datetime=now,
        review_duration=max(0, int(response_time_ms)),
    )
    serialized_card = json.loads(card.to_json())
    serialized_log = json.loads(review_log.to_json())
    due_naive = card.due.astimezone(timezone.utc).replace(tzinfo=None)
    interval_days = max(0.0, (due_naive - now_naive).total_seconds() / 86400.0)
    retrievability_after = scheduler.get_card_retrievability(card, now)
    user_card_state.fsrs_card_json = serialized_card
    user_card_state.fsrs_last_retrievability = retrievability_after
    user_card_state.fsrs_next_review_at = due_naive
    user_card_state.fsrs_interval_days = interval_days
    user_card_state.scheduler_shadow_version = FSRS_SHADOW_VERSION
    review_event.scheduler_shadow_version = FSRS_SHADOW_VERSION
    review_event.fsrs_predicted_recall = predicted_recall
    review_event.fsrs_next_review_at = due_naive
    review_event.fsrs_interval_days = interval_days
    review_event.fsrs_review_log_json = serialized_log
    return {
        "version": FSRS_SHADOW_VERSION,
        "predicted_recall_before": predicted_recall,
        "retrievability_after": retrievability_after,
        "next_review_at": due_naive,
        "interval_days": interval_days,
        "production_scheduler": "sm2",
        "shadow_scheduler": "fsrs6",
    }
