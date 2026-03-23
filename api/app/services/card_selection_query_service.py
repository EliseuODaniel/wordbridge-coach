"""Query helpers for card selection flows."""

from datetime import timedelta

from sqlalchemy import and_, func

from app.core.time import utc_now
from app.models import Card, ReviewEvent, Sentence, UserCardState, Word, WordFrequency


def get_recent_correct_word_ids(db, user_id: str, days: int = 7, limit: int = 50) -> set:
    """Return word ids answered correctly within the lookback window."""
    cutoff_date = utc_now() - timedelta(days=days)
    recent_correct = (
        db.query(ReviewEvent)
        .join(Card, ReviewEvent.card_id == Card.id)
        .join(Sentence, Card.sentence_id == Sentence.id)
        .filter(
            and_(
                ReviewEvent.user_id == user_id,
                ReviewEvent.created_at >= cutoff_date,
                ReviewEvent.was_correct == True,
            )
        )
        .distinct(Sentence.word_id)
        .limit(limit)
        .all()
    )

    return {
        review_event.card.sentence.word_id
        for review_event in recent_correct
        if review_event.card and review_event.card.sentence
    }


def get_due_review_candidates(
    db,
    *,
    user_id: str,
    target_language_id,
    target_language_code: str,
    max_contiguous_mastered_rank: int,
    max_count: int = 50,
    exclude_card_id=None,
):
    """Return due review candidates already gated to the unlocked prefix."""
    from app.models.user_card_state import MemoryStage

    query = (
        db.query(UserCardState, Word)
        .join(Card, UserCardState.card_id == Card.id)
        .join(Sentence, Card.sentence_id == Sentence.id)
        .join(Word, Sentence.word_id == Word.id)
        .filter(
            UserCardState.user_id == user_id,
            Word.language_id == target_language_id,
            UserCardState.next_review_at <= utc_now(),
            UserCardState.status.in_([MemoryStage.LEARNING, MemoryStage.REVIEW, MemoryStage.MATURE]),
        )
    )

    if max_contiguous_mastered_rank > 0:
        max_allowed_rank = max_contiguous_mastered_rank + 100
        query = query.join(
            WordFrequency,
            and_(
                func.lower(Word.lemma) == func.lower(WordFrequency.word),
                WordFrequency.language_code == target_language_code,
            ),
        ).filter(WordFrequency.rank <= max_allowed_rank)

    if exclude_card_id:
        query = query.filter(UserCardState.card_id != exclude_card_id)

    results = query.order_by(UserCardState.next_review_at).limit(max_count).all()
    return [(word, ucs) for ucs, word in results]


def get_due_relearn_candidate(db, user_id: str, exclude_card_id=None):
    """Return the next relearn candidate tuple ordered by due date."""
    query = (
        db.query(UserCardState, Word)
        .join(Card, UserCardState.card_id == Card.id)
        .join(Sentence, Card.sentence_id == Sentence.id)
        .join(Word, Sentence.word_id == Word.id)
        .filter(
            UserCardState.user_id == user_id,
            UserCardState.is_relearn == True,
            UserCardState.relearn_due <= utc_now(),
        )
    )

    if exclude_card_id:
        query = query.filter(UserCardState.card_id != exclude_card_id)

    return query.order_by(UserCardState.relearn_due).first()


def count_reviews_due(db, user_id: str) -> int:
    """Count non-new cards due for review."""
    from app.models.user_card_state import MemoryStage

    return (
        db.query(UserCardState)
        .filter(
            UserCardState.user_id == user_id,
            UserCardState.next_review_at <= utc_now(),
            UserCardState.status.in_([MemoryStage.LEARNING, MemoryStage.REVIEW, MemoryStage.MATURE]),
        )
        .count()
    )
