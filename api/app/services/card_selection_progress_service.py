"""Helpers for Spec4 progression updates after a submitted answer."""

from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User, Word, WordFrequency
from app.services.vocabulary_progression import VocabularyProgressionService


def get_target_language_code(db: Session, user_id: str) -> Optional[str]:
    """Resolve the user's target language code for progression updates."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.target_language_obj:
        return None
    return user.target_language_obj.code


def get_word_frequency_rank(
    db: Session,
    *,
    word_id: str,
    target_language_code: str,
) -> Optional[int]:
    """Look up the frequency rank for the answered word in the user's target language."""
    word = db.query(Word).filter(Word.id == word_id).first()
    if not word:
        return None

    word_frequency = db.query(WordFrequency).filter(
        func.lower(WordFrequency.word) == func.lower(word.lemma),
        WordFrequency.language_code == target_language_code,
    ).first()
    if not word_frequency:
        return None

    return word_frequency.rank


def record_selection_answer_progress(
    db: Session,
    *,
    user_id: str,
    word_id: str,
    was_correct: bool,
) -> Dict[str, Any]:
    """Advance Spec4 progression for correct answers without changing the API contract."""
    if not was_correct:
        return {"success": True, "message": "Incorrect answer, progression not updated"}

    target_language_code = get_target_language_code(db, user_id)
    if not target_language_code:
        return {"success": False, "error": "User not found"}

    rank = get_word_frequency_rank(
        db,
        word_id=word_id,
        target_language_code=target_language_code,
    )
    if rank is None:
        return {"success": False, "error": "WordFrequency not found"}

    progression_service = VocabularyProgressionService(db)
    progression_service.update_contiguous_mastered_rank(user_id, rank)
    return {"success": True, "rank": rank}
