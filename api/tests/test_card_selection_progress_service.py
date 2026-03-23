"""Tests for Spec4 progression helpers extracted from card selection."""

import uuid

from app.models import Word
from app.services import card_selection_progress_service


def test_record_selection_answer_progress_updates_contiguous_rank(
    db_session, test_user, sample_words, monkeypatch
):
    calls = []

    monkeypatch.setattr(
        card_selection_progress_service.VocabularyProgressionService,
        "update_contiguous_mastered_rank",
        lambda self, user_id, rank: calls.append((user_id, rank)),
    )

    result = card_selection_progress_service.record_selection_answer_progress(
        db_session,
        user_id=str(test_user.id),
        word_id=str(sample_words["en_book"].id),
        was_correct=True,
    )

    assert result == {"success": True, "rank": 100}
    assert calls == [(str(test_user.id), 100)]


def test_record_selection_answer_progress_skips_incorrect_answers():
    result = card_selection_progress_service.record_selection_answer_progress(
        db=object(),
        user_id="user-1",
        word_id="word-1",
        was_correct=False,
    )

    assert result == {
        "success": True,
        "message": "Incorrect answer, progression not updated",
    }


def test_record_selection_answer_progress_fails_without_matching_frequency(
    db_session, test_user, sample_languages
):
    word = Word(
        id=str(uuid.uuid4()),
        text="orphan",
        lemma="orphan",
        part_of_speech="noun",
        difficulty=1,
        language_id=sample_languages["en"].id,
        frequency_rank=999,
    )
    db_session.add(word)
    db_session.commit()

    result = card_selection_progress_service.record_selection_answer_progress(
        db_session,
        user_id=str(test_user.id),
        word_id=str(word.id),
        was_correct=True,
    )

    assert result == {"success": False, "error": "WordFrequency not found"}
