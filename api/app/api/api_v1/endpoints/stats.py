"""Stats endpoints for FillTheWord."""

from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.time import utc_now, utc_today
from app.models import Card, ReviewEvent, Sentence, UserCardState, Word
from app.models.user_card_state import MemoryStage
from app.services.request_user_service import get_request_user

router = APIRouter()


class StatsResponse(BaseModel):
    """Response model for basic stats."""

    cards_total: int
    new_count: int
    learning_count: int
    review_count: int
    mature_count: int
    reviews_today: int
    accuracy_today: float
    new_cards_today: int
    upcoming_reviews: dict


@router.get('/basic', response_model=StatsResponse)
async def get_basic_stats(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get basic statistics for an explicit persisted user."""
    try:
        user = get_request_user(db, user_id)
        resolved_user_id = user.id

        cards_total = db.query(Card).join(Sentence).join(Word).filter(
            and_(
                Card.is_active == True,
                Word.language_id == user.target_language_id,
            )
        ).count()

        stage_counts = db.query(
            UserCardState.status,
            func.count(UserCardState.id).label('count'),
        ).join(Card).join(Sentence).join(Word).filter(
            and_(
                UserCardState.user_id == resolved_user_id,
                Card.is_active == True,
                Word.language_id == user.target_language_id,
            )
        ).group_by(UserCardState.status).all()

        new_count = 0
        learning_count = 0
        review_count = 0
        mature_count = 0

        for status, count in stage_counts:
            if status == MemoryStage.NEW:
                new_count = count
            elif status == MemoryStage.LEARNING:
                learning_count = count
            elif status == MemoryStage.REVIEW:
                review_count = count
            elif status == MemoryStage.MATURE:
                mature_count = count

        today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        reviews_today = db.query(ReviewEvent).filter(
            and_(
                ReviewEvent.user_id == resolved_user_id,
                ReviewEvent.created_at >= today_start,
            )
        ).count()

        correct_today = db.query(ReviewEvent).filter(
            and_(
                ReviewEvent.user_id == resolved_user_id,
                ReviewEvent.created_at >= today_start,
                ReviewEvent.was_correct == True,
            )
        ).count()

        accuracy_today = correct_today / max(reviews_today, 1)

        cards_seen_today = db.query(func.distinct(ReviewEvent.card_id)).filter(
            and_(
                ReviewEvent.user_id == resolved_user_id,
                func.date(ReviewEvent.created_at) == func.current_date(),
            )
        ).subquery()

        cards_seen_before_today = db.query(func.distinct(ReviewEvent.card_id)).filter(
            and_(
                ReviewEvent.user_id == resolved_user_id,
                func.date(ReviewEvent.created_at) < func.current_date(),
            )
        ).subquery()

        new_cards_today = db.query(Card.id).filter(
            and_(
                Card.id.in_(cards_seen_today),
                ~Card.id.in_(cards_seen_before_today),
            )
        ).count() or 0

        upcoming_start = utc_today()
        upcoming_end = upcoming_start + timedelta(days=7)

        upcoming_reviews = db.query(
            func.date(UserCardState.next_review_at).label('review_date'),
            func.count(UserCardState.id).label('count'),
        ).join(Card).join(Sentence).join(Word).filter(
            and_(
                UserCardState.user_id == resolved_user_id,
                Card.is_active == True,
                Word.language_id == user.target_language_id,
                UserCardState.next_review_at.between(upcoming_start, upcoming_end),
            )
        ).group_by(func.date(UserCardState.next_review_at)).all()

        upcoming_dict = {str(review_date): count for review_date, count in upcoming_reviews}
        for i in range(7):
            date_str = str(upcoming_start + timedelta(days=i))
            if date_str not in upcoming_dict:
                upcoming_dict[date_str] = 0

        return StatsResponse(
            cards_total=cards_total,
            new_count=new_count,
            learning_count=learning_count,
            review_count=review_count,
            mature_count=mature_count,
            reviews_today=reviews_today,
            accuracy_today=accuracy_today,
            new_cards_today=new_cards_today,
            upcoming_reviews=upcoming_dict,
        )
    except HTTPException:
        raise
    except Exception as exc:
        print(f'Error in get_basic_stats: {exc}')
        raise HTTPException(status_code=500, detail='Internal server error')


@router.get('/health')
async def health_check():
    """Health check for stats service."""
    return {'status': 'healthy', 'service': 'stats-api'}
