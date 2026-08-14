"""Focused tests for vocabulary progression language-aware behavior."""

from datetime import timedelta
from types import SimpleNamespace
import uuid

from app.models import (
    Card,
    ReviewEvent,
    Sentence,
    Word,
    WordFrequency,
)
from app.models.sentence import SourceType
from app.core.time import utc_now

from app.services.vocabulary_progression import VocabularyProgressionService


def test_review_score_uses_ordered_history_without_per_word_queries():
    now = utc_now()
    reviews = [
        SimpleNamespace(created_at=now - timedelta(days=1), was_correct=False),
        SimpleNamespace(created_at=now - timedelta(days=4), was_correct=True),
        SimpleNamespace(created_at=now - timedelta(days=2), was_correct=False),
    ]

    score = VocabularyProgressionService._calculate_review_score(reviews)

    assert score > 0.7
    assert VocabularyProgressionService._calculate_review_score([]) == 1.0


def test_missing_valid_cloze_does_not_generate_unsafe_fallback(db_session, sample_languages):
    word = Word(
        id=str(uuid.uuid4()),
        text="placeholder",
        lemma="placeholder",
        part_of_speech="noun",
        difficulty=1,
        language_id=sample_languages["en"].id,
        frequency_rank=999,
    )
    invalid_sentence = Sentence(
        id=str(uuid.uuid4()),
        text="This sentence has no gap.",
        translation="Esta frase não tem lacuna.",
        gap_start=0,
        gap_end=0,
        language_id=sample_languages["en"].id,
        word_id=word.id,
        type="FILL_IN_THE_GAP",
        source_type=SourceType.GENERATED,
        difficulty=1,
        quality_status="needs_review",
    )
    db_session.add_all([word, invalid_sentence])
    db_session.commit()
    before_count = db_session.query(Sentence).filter(Sentence.word_id == word.id).count()

    selected = VocabularyProgressionService(db_session).get_sentence_for_word("unused-user", word.id)

    assert selected is None
    assert db_session.query(Sentence).filter(Sentence.word_id == word.id).count() == before_count


def test_get_next_new_word_rank_respects_target_language(
    db_session, test_user, test_user_french, sample_words
):
    """English and French users should resolve their next rank from their own language."""
    service = VocabularyProgressionService(db_session)

    en_progress = service.get_or_create_user_progress(str(test_user.id))
    fr_progress = service.get_or_create_user_progress(str(test_user_french.id))

    assert service.get_next_new_word_rank(str(test_user.id), en_progress) == 50
    assert service.get_next_new_word_rank(str(test_user_french.id), fr_progress) == 100


def test_get_due_review_words_respects_target_language(
    db_session, test_user, test_user_french, sample_words
):
    """Review candidates should come from the user's target language, not a hardcoded one."""
    service = VocabularyProgressionService(db_session)

    en_words = service.get_due_review_words(str(test_user.id), max_rank=150)
    fr_words = service.get_due_review_words(str(test_user_french.id), max_rank=150)

    assert {word.lemma for word in en_words} == {"there", "book", "house"}
    assert {word.lemma for word in fr_words} == {"livre", "maison"}


def test_update_contiguous_mastered_rank_ignores_reviews_from_other_language(
    db_session, sample_languages, test_user_french, sample_words, sample_decks
):
    """French progression should not advance using an English review at the next rank."""
    service = VocabularyProgressionService(db_session)
    progress = service.get_or_create_user_progress(str(test_user_french.id))
    progress.max_contiguous_mastered_rank = 99
    db_session.commit()

    english_word = Word(
        id=str(uuid.uuid4()),
        text="bridge",
        lemma="bridge",
        part_of_speech="noun",
        difficulty=1,
        language_id=sample_languages["en"].id,
        frequency_rank=101,
    )
    english_frequency = WordFrequency(
        word="bridge",
        language_code="en",
        rank=101,
        coverage_pct=50.0,
        band=1,
        frequency_score=0.899,
        is_active=True,
    )
    english_sentence = Sentence(
        id=str(uuid.uuid4()),
        text="The ___ is long.",
        translation="A ponte é longa.",
        grammar_hint="noun",
        gap_start=4,
        gap_end=10,
        language_id=sample_languages["en"].id,
        word_id=english_word.id,
        type="FILL_IN_THE_GAP",
        source_type=SourceType.CORPUS,
        difficulty=1,
    )
    english_card = Card(
        id=str(uuid.uuid4()),
        sentence_id=english_sentence.id,
        deck_id=sample_decks["en"].id,
        grammar_hint="noun",
        gap_start=4,
        gap_end=10,
        is_active=True,
        difficulty=1,
    )
    english_review = ReviewEvent(
        id=str(uuid.uuid4()),
        user_id=test_user_french.id,
        card_id=english_card.id,
        sentence_id=english_sentence.id,
        quality=5,
        response_time_ms=1200,
        user_answer="bridge",
        correct_answer="bridge",
        was_correct=True,
        attempts=1,
        hints_used=0,
    )

    db_session.add_all(
        [english_word, english_frequency, english_sentence, english_card, english_review]
    )
    db_session.commit()

    service.update_contiguous_mastered_rank(str(test_user_french.id), 100)
    db_session.refresh(progress)

    assert progress.max_contiguous_mastered_rank == 100
