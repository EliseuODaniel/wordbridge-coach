"""Tests for Lingvist difficulty progression helpers."""

from types import SimpleNamespace
import uuid

from app.models import Sentence
from app.models.sentence import SourceType
from app.services.lingvist_difficulty_service import (
    choose_frequency_ordered_new_word,
    get_lingvist_difficulty_profile,
)
from app.services.vocabulary_progression import VocabularyProgressionService


def test_lingvist_profile_grows_sentence_complexity():
    foundation = get_lingvist_difficulty_profile(
        max_contiguous_mastered_rank=0,
        current_window_end_rank=100,
    )
    expanding = get_lingvist_difficulty_profile(
        max_contiguous_mastered_rank=900,
        current_window_end_rank=1000,
    )

    assert foundation.phase == "foundation"
    assert foundation.max_word_count < expanding.max_word_count
    assert foundation.target_sentence_difficulty < expanding.target_sentence_difficulty
    assert foundation.ranked_candidate_pool < expanding.ranked_candidate_pool
    assert foundation.pace_hint == "balance"


def test_lingvist_profile_slows_down_when_support_is_needed():
    profile = get_lingvist_difficulty_profile(
        max_contiguous_mastered_rank=900,
        current_window_end_rank=1000,
        recent_accuracy=0.52,
        review_pressure="high",
        difficulty_signal="support_needed",
    )

    assert profile.pace_hint == "stabilize"
    assert profile.support_bias == "support_needed"
    assert profile.target_sentence_difficulty == 2
    assert profile.max_word_count == 14


def test_lingvist_profile_stretches_when_user_is_ready():
    profile = get_lingvist_difficulty_profile(
        max_contiguous_mastered_rank=900,
        current_window_end_rank=1000,
        recent_accuracy=0.93,
        review_pressure="low",
        difficulty_signal="ready_to_push",
    )

    assert profile.pace_hint == "accelerate"
    assert profile.support_bias == "ready_to_push"
    assert profile.target_sentence_difficulty == 4
    assert profile.max_word_count == 18


def test_choose_frequency_ordered_new_word_uses_frequency_sorted_lookahead(monkeypatch):
    ranked_candidates = [
        (SimpleNamespace(id="w-100"), 100),
        (SimpleNamespace(id="w-50"), 50),
        (SimpleNamespace(id="w-150"), 150),
    ]
    captured = {}

    def fake_choices(population, weights, k):
        captured["population"] = population
        captured["weights"] = weights
        return [population[0]]

    monkeypatch.setattr(
        "app.services.lingvist_difficulty_service.random.choices",
        fake_choices,
    )

    chosen = choose_frequency_ordered_new_word(
        ranked_candidates,
        excluded_word_ids=set(),
        pool_size=3,
    )

    assert chosen.id == "w-50"
    assert [word.id for word, _ in captured["population"]] == ["w-50", "w-100", "w-150"]
    assert captured["weights"] == [3, 2, 1]


def test_choose_frequency_ordered_new_word_skips_excluded_candidates():
    ranked_candidates = [
        (SimpleNamespace(id="w-50"), 50),
        (SimpleNamespace(id="w-100"), 100),
    ]

    chosen = choose_frequency_ordered_new_word(
        ranked_candidates,
        excluded_word_ids={"w-50"},
        pool_size=3,
    )

    assert chosen.id == "w-100"


def test_choose_frequency_ordered_new_word_allows_lookahead_variety(monkeypatch):
    ranked_candidates = [
        (SimpleNamespace(id="w-10"), 10),
        (SimpleNamespace(id="w-20"), 20),
        (SimpleNamespace(id="w-30"), 30),
    ]

    monkeypatch.setattr(
        "app.services.lingvist_difficulty_service.random.choices",
        lambda population, weights, k: [population[1]],
    )

    chosen = choose_frequency_ordered_new_word(
        ranked_candidates,
        excluded_word_ids=set(),
        pool_size=3,
    )

    assert chosen.id == "w-20"


def test_lingvist_sentence_selection_prefers_easier_sentence_early_and_richer_sentence_later(
    db_session,
    sample_languages,
    sample_words,
    sample_sentences,
    test_user,
):
    service = VocabularyProgressionService(db_session)
    progress = service.get_or_create_user_progress(str(test_user.id))
    word = sample_words["en_book"]
    easy_sentence = sample_sentences["en_book"]

    harder_sentence = Sentence(
        id=str(uuid.uuid4()),
        text="Although the ___ lay forgotten beneath the dust-covered lamp, I still hoped to finish it before dawn.",
        translation="Embora o livro estivesse esquecido sob a luminária coberta de pó, eu ainda esperava terminá-lo antes do amanhecer.",
        grammar_hint="noun - object",
        gap_start=13,
        gap_end=16,
        language_id=sample_languages["en"].id,
        word_id=word.id,
        type="FILL_IN_THE_GAP",
        source_type=SourceType.CORPUS,
        difficulty=4,
        source_title="Pride and Prejudice",
    )
    db_session.add(harder_sentence)
    db_session.commit()

    progress.max_contiguous_mastered_rank = 0
    progress.current_window_end_rank = 100
    db_session.commit()
    early_choice = service.get_sentence_for_word(
        str(test_user.id),
        word.id,
        use_lingvist_profile=True,
    )

    progress.max_contiguous_mastered_rank = 1200
    progress.current_window_end_rank = 1500
    db_session.commit()
    later_choice = service.get_sentence_for_word(
        str(test_user.id),
        word.id,
        use_lingvist_profile=True,
    )

    assert early_choice.id == easy_sentence.id
    assert later_choice.id == harder_sentence.id
