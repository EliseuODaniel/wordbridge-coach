"""Fallback and legacy lookup helpers for card selection."""

from sqlalchemy import and_, func

from app.models import Card, Sentence, UserCardState, Word, WordFrequency


def find_any_eligible_card(
    db,
    *,
    target_language_id,
    target_language_code: str,
    max_rank: int,
    user_id: str,
    exclude_card_id=None,
):
    """Return a random eligible card within the unlocked range."""
    query = (
        db.query(Card)
        .join(Sentence, Card.sentence_id == Sentence.id)
        .join(Word, Sentence.word_id == Word.id)
        .filter(
            Card.is_active == True,
            Word.language_id == target_language_id,
        )
        .join(
            WordFrequency,
            and_(
                func.lower(Word.lemma) == func.lower(WordFrequency.word),
                WordFrequency.language_code == target_language_code,
                WordFrequency.rank <= max_rank,
            ),
        )
    )

    if exclude_card_id:
        query = query.filter(Card.id != exclude_card_id)

    return query.order_by(func.random()).first()


def get_card_review_state(db, *, user_id: str, card_id: str):
    """Return the stored card review state for a user when present."""
    return (
        db.query(UserCardState)
        .filter(
            UserCardState.user_id == user_id,
            UserCardState.card_id == card_id,
        )
        .first()
    )


def get_word_by_rank(
    db,
    *,
    rank: int,
    target_language_code: str,
    max_allowed_rank=None,
    max_unlocked_rank=None,
    excluded_word_id=None,
):
    """Legacy rank lookup with deterministic fallback inside the allowed window."""
    if max_unlocked_rank and rank > max_unlocked_rank + 50:
        return None

    query = (
        db.query(Word)
        .join(
            WordFrequency,
            and_(
                func.lower(Word.lemma) == func.lower(WordFrequency.word),
                WordFrequency.language_code == target_language_code,
            ),
        )
        .filter(WordFrequency.rank == rank)
    )
    word = query.first()

    if word:
        if max_allowed_rank and rank > max_allowed_rank:
            return None
        if excluded_word_id and str(word.id) == str(excluded_word_id):
            return None
        return word

    if max_allowed_rank:
        next_available = (
            db.query(WordFrequency)
            .filter(
                and_(
                    WordFrequency.rank >= rank,
                    WordFrequency.rank <= max_allowed_rank,
                    WordFrequency.language_code == target_language_code,
                )
            )
            .order_by(WordFrequency.rank)
            .first()
        )

        if next_available:
            return (
                db.query(Word)
                .join(
                    WordFrequency,
                    and_(
                        func.lower(Word.lemma) == func.lower(WordFrequency.word),
                        WordFrequency.language_code == target_language_code,
                    ),
                )
                .filter(WordFrequency.rank == next_available.rank)
                .first()
            )

    return None
