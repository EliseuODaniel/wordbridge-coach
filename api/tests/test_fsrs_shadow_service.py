from datetime import datetime, timezone
from types import SimpleNamespace

from app.core.time import utc_now
from app.services.fsrs_shadow_service import apply_fsrs_shadow, quality_to_rating
from fsrs import Rating


def _state():
    return SimpleNamespace(
        fsrs_card_json=None,
        fsrs_last_retrievability=None,
        fsrs_next_review_at=None,
        fsrs_interval_days=None,
        scheduler_shadow_version=None,
    )


def _event():
    return SimpleNamespace(
        scheduler_shadow_version=None,
        fsrs_predicted_recall=None,
        fsrs_next_review_at=None,
        fsrs_interval_days=None,
        fsrs_review_log_json=None,
    )


def test_fsrs_shadow_updates_telemetry_without_production_due_date():
    state = _state()
    event = _event()
    result = apply_fsrs_shadow(
        state,
        event,
        quality=4,
        response_time_ms=1200,
        reviewed_at=utc_now(),
    )
    assert result["production_scheduler"] == "sm2"
    assert result["shadow_scheduler"] == "fsrs6"
    assert state.fsrs_card_json
    assert event.fsrs_review_log_json
    assert event.fsrs_next_review_at == state.fsrs_next_review_at


def test_quality_mapping_is_conservative():
    assert quality_to_rating(0) == Rating.Again
    assert quality_to_rating(3) == Rating.Hard
    assert quality_to_rating(4) == Rating.Good
    assert quality_to_rating(5) == Rating.Easy


def test_fsrs_shadow_accepts_timezone_aware_review_times():
    result = apply_fsrs_shadow(
        _state(),
        _event(),
        quality=4,
        response_time_ms=800,
        reviewed_at=datetime.now(timezone.utc),
    )
    assert result["interval_days"] >= 0
