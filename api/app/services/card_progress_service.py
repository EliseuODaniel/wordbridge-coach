"""Helpers for post-answer progress updates in the cards flow."""

from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.time import utc_now, utc_today
from app.models import ReviewEvent, User, UserCardState
from app.models.user_daily_stats import UserDailyStats
from app.models.user_theme_stats import UserThemeStats
from app.models.word_theme_mapping import WordThemeMapping
from app.services.card_selection_progress_service import record_selection_answer_progress
from app.services.sm2 import SM2Algorithm


def get_or_create_daily_stats(db: Session, user_id: str) -> UserDailyStats:
    """Load today's stats row, creating it if needed."""
    today = utc_today()
    daily_stats = db.query(UserDailyStats).filter(
        UserDailyStats.user_id == user_id,
        UserDailyStats.date == today,
    ).first()

    if daily_stats:
        return daily_stats

    daily_stats = UserDailyStats(
        user_id=user_id,
        date=today,
        cards_answered=0,
        new_words_learned=0,
        reviews_done=0,
        accuracy=0.0,
    )
    db.add(daily_stats)
    db.flush()
    return daily_stats


def update_user_accuracy_last_20(db: Session, user_id: str, is_correct: bool) -> Optional[User]:
    """Recompute rolling accuracy for the latest twenty answers."""
    from sqlalchemy import desc

    recent_20 = (
        db.query(ReviewEvent)
        .filter(ReviewEvent.user_id == user_id)
        .order_by(desc(ReviewEvent.created_at))
        .limit(19)
        .all()
    )

    correct_count = sum(1 for review in recent_20 if review.was_correct)
    if is_correct:
        correct_count += 1

    total_count = len(recent_20) + 1
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    user.accuracy_last_20 = correct_count / total_count if total_count > 0 else None
    return user


def update_relearn_state(
    db: Session,
    user: Optional[User],
    user_card_state: UserCardState,
    card_id: str,
    user_id: str,
    quality: int,
) -> None:
    """Apply Lingvist relearn queue updates for the reviewed card."""
    if not user or user.mode != "lingvist":
        return

    should_relearn = SM2Algorithm.should_enter_relearn(quality)

    if should_relearn:
        user_card_state.is_relearn = True

        relearn_count = (
            db.query(ReviewEvent)
            .filter(
                ReviewEvent.user_id == user_id,
                ReviewEvent.card_id == card_id,
                ReviewEvent.quality < 3,
            )
            .count()
        )

        relearn_interval = SM2Algorithm.calculate_relearn_interval(relearn_count)
        user_card_state.relearn_due = utc_now() + relearn_interval
        return

    if user_card_state.is_relearn:
        user_card_state.is_relearn = False
        user_card_state.relearn_due = None


def update_theme_stats(
    db: Session,
    user_id: str,
    word_id: str,
    was_correct: bool,
    response_time_ms: int,
) -> None:
    """Update theme stats for every active theme linked to the reviewed word."""
    theme_mappings = db.query(WordThemeMapping.theme_id).filter(
        and_(
            WordThemeMapping.word_id == word_id,
            WordThemeMapping.is_active == True,
        )
    ).all()

    for theme_mapping in theme_mappings:
        theme_id = theme_mapping[0]

        theme_stats = db.query(UserThemeStats).filter(
            and_(
                UserThemeStats.user_id == user_id,
                UserThemeStats.theme_id == theme_id,
            )
        ).first()

        if not theme_stats:
            theme_stats = UserThemeStats(
                user_id=user_id,
                theme_id=theme_id,
                attempts=0,
                correct=0,
                accuracy=0.0,
                avg_response_time_ms=0.0,
            )
            db.add(theme_stats)
            db.flush()

        theme_stats.add_attempt(
            was_correct=was_correct,
            response_time_ms=response_time_ms,
        )


def record_spec4_progress(
    db: Session,
    *,
    user_id: str,
    word_id: str,
    sentence_id: str,
    was_correct: bool,
    response_time_ms: int,
    quality: int,
) -> bool:
    """Update Spec4 progression without breaking answer submission on failure."""
    if not was_correct:
        return False

    try:
        record_selection_answer_progress(
            db,
            user_id=user_id,
            word_id=word_id,
            was_correct=was_correct,
        )
        return True
    except Exception:
        return False


def apply_post_answer_updates(
    db: Session,
    *,
    user_id: str,
    card_id: str,
    word_id: str,
    sentence_id: str,
    user_card_state: UserCardState,
    is_correct: bool,
    quality: int,
    response_time_ms: int,
) -> None:
    """Apply stats and progression side effects after the answer core state is ready."""
    daily_stats = get_or_create_daily_stats(db, user_id)
    daily_stats.update_accuracy(was_correct=is_correct)
    if is_correct:
        daily_stats.add_new_word()

    user = update_user_accuracy_last_20(db, user_id, is_correct)
    update_relearn_state(db, user, user_card_state, card_id, user_id, quality)
    update_theme_stats(
        db=db,
        user_id=user_id,
        word_id=word_id,
        was_correct=is_correct,
        response_time_ms=response_time_ms,
    )
    record_spec4_progress(
        db,
        user_id=user_id,
        word_id=word_id,
        sentence_id=sentence_id,
        was_correct=is_correct,
        response_time_ms=response_time_ms,
        quality=quality,
    )
