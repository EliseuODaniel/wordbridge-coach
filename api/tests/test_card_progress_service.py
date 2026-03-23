"""Tests for post-answer stats and progression orchestration."""

from types import SimpleNamespace

from app.services import card_progress_service


def test_apply_post_answer_updates_calls_expected_helpers(monkeypatch):
    calls = []

    class FakeDailyStats:
        def update_accuracy(self, was_correct):
            calls.append(("update_accuracy", was_correct))

        def add_new_word(self):
            calls.append(("add_new_word",))

    fake_daily_stats = FakeDailyStats()
    fake_user = SimpleNamespace(mode="lingvist")
    fake_state = SimpleNamespace()

    monkeypatch.setattr(
        card_progress_service,
        "get_or_create_daily_stats",
        lambda db, user_id: fake_daily_stats,
    )
    monkeypatch.setattr(
        card_progress_service,
        "update_user_accuracy_last_20",
        lambda db, user_id, is_correct: fake_user,
    )
    monkeypatch.setattr(
        card_progress_service,
        "update_relearn_state",
        lambda db, user, user_card_state, card_id, user_id, quality: calls.append(
            ("update_relearn_state", card_id, user_id, quality)
        ),
    )
    monkeypatch.setattr(
        card_progress_service,
        "update_theme_stats",
        lambda db, user_id, word_id, was_correct, response_time_ms: calls.append(
            ("update_theme_stats", user_id, word_id, was_correct, response_time_ms)
        ),
    )
    monkeypatch.setattr(
        card_progress_service,
        "record_spec4_progress",
        lambda db, **kwargs: calls.append(("record_spec4_progress", kwargs["word_id"], kwargs["was_correct"])),
    )

    card_progress_service.apply_post_answer_updates(
        db=object(),
        user_id="user-1",
        card_id="card-1",
        word_id="word-1",
        sentence_id="sentence-1",
        user_card_state=fake_state,
        is_correct=True,
        quality=4,
        response_time_ms=1800,
    )

    assert calls == [
        ("update_accuracy", True),
        ("add_new_word",),
        ("update_relearn_state", "card-1", "user-1", 4),
        ("update_theme_stats", "user-1", "word-1", True, 1800),
        ("record_spec4_progress", "word-1", True),
    ]


def test_record_spec4_progress_skips_incorrect_answers():
    result = card_progress_service.record_spec4_progress(
        db=object(),
        user_id="user-1",
        word_id="word-1",
        sentence_id="sentence-1",
        was_correct=False,
        response_time_ms=1800,
        quality=2,
    )

    assert result is False
