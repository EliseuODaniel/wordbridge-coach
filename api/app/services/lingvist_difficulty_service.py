"""Difficulty progression helpers for Lingvist mode."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import random
import re
from typing import Iterable, Sequence

from app.models.sentence import SourceType

_WORD_RE = re.compile(r"[A-Za-zÀ-ÿ']+")


@dataclass(frozen=True)
class LingvistDifficultyProfile:
    """Profile describing the next Lingvist learning phase."""

    phase: str
    rank_limit: int
    sentence_difficulty_min: int
    sentence_difficulty_max: int
    target_sentence_difficulty: int
    min_word_count: int
    max_word_count: int
    ranked_candidate_pool: int
    pace_hint: str
    support_bias: str


def get_lingvist_difficulty_profile(
    *,
    max_contiguous_mastered_rank: int,
    current_window_end_rank: int,
    recent_accuracy: float | None = None,
    review_pressure: str | None = None,
    difficulty_signal: str | None = None,
) -> LingvistDifficultyProfile:
    """Return the current Lingvist difficulty phase for a learner.

    The thresholds are inspired by Lingvist's frequency-first sequencing, where
    early phases focus on very common words in short/high-signal contexts and
    later phases gradually introduce longer and denser sentences.
    """
    exposure_rank = max(max_contiguous_mastered_rank, current_window_end_rank)

    if exposure_rank <= 100:
        base_profile = LingvistDifficultyProfile(
            phase="foundation",
            rank_limit=100,
            sentence_difficulty_min=1,
            sentence_difficulty_max=2,
            target_sentence_difficulty=1,
            min_word_count=4,
            max_word_count=9,
            ranked_candidate_pool=6,
            pace_hint="balance",
            support_bias="on_target",
        )
    elif exposure_rank <= 500:
        base_profile = LingvistDifficultyProfile(
            phase="building",
            rank_limit=500,
            sentence_difficulty_min=1,
            sentence_difficulty_max=3,
            target_sentence_difficulty=2,
            min_word_count=5,
            max_word_count=12,
            ranked_candidate_pool=8,
            pace_hint="balance",
            support_bias="on_target",
        )
    elif exposure_rank <= 1500:
        base_profile = LingvistDifficultyProfile(
            phase="expanding",
            rank_limit=1500,
            sentence_difficulty_min=2,
            sentence_difficulty_max=4,
            target_sentence_difficulty=3,
            min_word_count=7,
            max_word_count=16,
            ranked_candidate_pool=10,
            pace_hint="balance",
            support_bias="on_target",
        )
    else:
        base_profile = LingvistDifficultyProfile(
            phase="nuanced",
            rank_limit=10000,
            sentence_difficulty_min=3,
            sentence_difficulty_max=5,
            target_sentence_difficulty=4,
            min_word_count=9,
            max_word_count=22,
            ranked_candidate_pool=12,
            pace_hint="balance",
            support_bias="on_target",
        )

    if difficulty_signal == "support_needed" or review_pressure == "high" or (
        recent_accuracy is not None and recent_accuracy < 0.6
    ):
        return LingvistDifficultyProfile(
            phase=base_profile.phase,
            rank_limit=base_profile.rank_limit,
            sentence_difficulty_min=max(1, base_profile.sentence_difficulty_min - 1),
            sentence_difficulty_max=max(base_profile.sentence_difficulty_min, base_profile.sentence_difficulty_max - 1),
            target_sentence_difficulty=max(1, base_profile.target_sentence_difficulty - 1),
            min_word_count=max(3, base_profile.min_word_count - 1),
            max_word_count=max(base_profile.min_word_count, base_profile.max_word_count - 2),
            ranked_candidate_pool=max(4, base_profile.ranked_candidate_pool - 2),
            pace_hint="stabilize",
            support_bias="support_needed",
        )

    if difficulty_signal == "ready_to_push" and review_pressure != "high" and (
        recent_accuracy is None or recent_accuracy >= 0.85
    ):
        return LingvistDifficultyProfile(
            phase=base_profile.phase,
            rank_limit=base_profile.rank_limit,
            sentence_difficulty_min=base_profile.sentence_difficulty_min,
            sentence_difficulty_max=min(5, base_profile.sentence_difficulty_max + 1),
            target_sentence_difficulty=min(5, base_profile.target_sentence_difficulty + 1),
            min_word_count=base_profile.min_word_count,
            max_word_count=base_profile.max_word_count + 2,
            ranked_candidate_pool=base_profile.ranked_candidate_pool + 2,
            pace_hint="accelerate",
            support_bias="ready_to_push",
        )

    return base_profile


def count_sentence_words(text: str | None) -> int:
    """Count natural-language tokens while ignoring the cloze placeholder."""
    if not text:
        return 0

    normalized = text.replace("___", "")
    return len(_WORD_RE.findall(normalized))


def score_sentence_candidate(
    *,
    sentence,
    profile: LingvistDifficultyProfile,
    usage_count: int,
    last_used_at: datetime | None,
) -> float:
    """Score a sentence for Lingvist mode.

    Higher scores mean: shorter/easier in early phases, more variety, real
    source material preferred, and generated fallback sentences strongly
    deprioritized.
    """
    word_count = count_sentence_words(getattr(sentence, "text", ""))
    difficulty = int(getattr(sentence, "difficulty", profile.target_sentence_difficulty) or profile.target_sentence_difficulty)
    source_type = getattr(sentence, "source_type", SourceType.CORPUS)
    source_title = getattr(sentence, "source_title", None)
    quality_status = str(getattr(sentence, "quality_status", "unreviewed") or "unreviewed")
    is_contemporary = bool(getattr(sentence, "is_contemporary", False))

    score = 0.0

    if usage_count == 0:
        score += 14.0
    else:
        score += max(0.0, 8.0 - (usage_count * 1.75))

    if last_used_at is not None:
        score += 0.25

    if profile.sentence_difficulty_min <= difficulty <= profile.sentence_difficulty_max:
        score += 10.0 - abs(profile.target_sentence_difficulty - difficulty) * 2.5
    else:
        score -= 6.0 + abs(profile.target_sentence_difficulty - difficulty) * 3.0

    if profile.min_word_count <= word_count <= profile.max_word_count:
        midpoint = (profile.min_word_count + profile.max_word_count) / 2.0
        score += 8.0 - abs(word_count - midpoint) * 0.8
    else:
        if word_count < profile.min_word_count:
            score -= (profile.min_word_count - word_count) * 2.2
        else:
            score -= (word_count - profile.max_word_count) * 1.7

    if source_type == SourceType.MANUAL:
        score += 4.0
    elif source_type == SourceType.CORPUS:
        score += 3.0
    else:
        score -= 5.0

    if source_title:
        score += 2.0
    if quality_status == "approved":
        score += 8.0
    elif quality_status == "literary":
        score += 1.0
    elif quality_status == "needs_review":
        score -= 12.0
    elif quality_status == "rejected":
        score -= 1000.0
    if is_contemporary:
        score += 5.0

    punctuation_marks = sum(1 for mark in ",?!;:" if mark in (getattr(sentence, "text", "") or ""))
    if punctuation_marks:
        score += min(1.5, punctuation_marks * 0.5)

    return score


def choose_sentence_for_lingvist(
    sentences: Sequence,
    *,
    profile: LingvistDifficultyProfile,
    usage_counts: dict,
    last_used_lookup: dict,
) -> object | None:
    """Choose a varied sentence among the best-scoring candidates for the phase."""
    if not sentences:
        return None

    scored_pairs = [
        (
            sentence,
            score_sentence_candidate(
                sentence=sentence,
                profile=profile,
                usage_count=usage_counts.get(sentence.id, 0),
                last_used_at=last_used_lookup.get(sentence.id),
            ),
        )
        for sentence in sentences
    ]
    scored_pairs.sort(
        key=lambda item: (item[1], getattr(item[0], "created_at", None) or datetime.min),
        reverse=True,
    )

    best_score = scored_pairs[0][1]
    eligible = [sentence for sentence, score in scored_pairs if score >= best_score - 1.5][:3]
    return random.choice(eligible)


def choose_frequency_ordered_new_word(candidates: Iterable, *, excluded_word_ids: set[str], pool_size: int) -> object | None:
    """Select the next Lingvist new word by descending frequency.

    Frequency rank 1 is the most common word, so we traverse candidates in
    ascending rank order and allow a small weighted lookahead window for
    variety without losing the frequency-first bias.
    """
    ranked = []
    for candidate in candidates:
        word, rank = candidate
        word_id = str(getattr(word, "id", ""))
        if word_id in excluded_word_ids:
            continue
        ranked.append((word, int(rank)))

    if not ranked:
        return None

    ranked.sort(key=lambda item: item[1])
    pool = ranked[: max(1, pool_size)]
    weights = [len(pool) - index for index in range(len(pool))]
    chosen_word, _ = random.choices(pool, weights=weights, k=1)[0]
    return chosen_word
