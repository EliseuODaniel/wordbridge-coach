"""Stats endpoints for FillTheWord"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, DATE
from datetime import timedelta
import uuid

from app.core.database import get_db
from app.core.time import utc_now, utc_today
from app.models import User, UserCardState, Card, ReviewEvent, Sentence, Word, Language
from app.models.user_card_state import MemoryStage
from pydantic import BaseModel

router = APIRouter()


class StatsResponse(BaseModel):
    """Response model for basic stats"""
    cards_total: int
    new_count: int
    learning_count: int
    review_count: int
    mature_count: int
    reviews_today: int
    accuracy_today: float
    new_cards_today: int
    upcoming_reviews: dict


class SettingsResponse(BaseModel):
    """Response model for user settings"""
    daily_new_limit: int
    easiness_factor: float


class SettingsUpdate(BaseModel):
    """Request model for updating settings"""
    daily_new_limit: Optional[int] = None
    easiness_factor: Optional[float] = None


def get_demo_user(db: Session) -> User:
    """Get or create demo user"""
    user = db.query(User).filter(User.username == "demo").first()
    if not user:
        # Create demo user if not exists
        en_lang = db.query(Language).filter(Language.code == "en").first()
        pt_lang = db.query(Language).filter(Language.code == "pt").first()

        if not en_lang:
            en_lang = Language(
                id=str(uuid.uuid4()),
                code="en",
                name="English",
                voice_model="lessac-glow_tts",
                voice_type="female",
                is_active=True
            )
            db.add(en_lang)
            db.flush()

        if not pt_lang:
            pt_lang = Language(
                id=str(uuid.uuid4()),
                code="pt",
                name="Portuguese",
                voice_model="lessac-glow_tts",
                voice_type="female",
                is_active=True
            )
            db.add(pt_lang)
            db.flush()

        user = User(
            id=str(uuid.uuid4()),
            username="demo",
            email="demo@filltheword.com",
            native_language_id=en_lang.id,
            target_language_id=pt_lang.id,
            language_preference="en",
            daily_new_limit=10,
            easiness_factor=2.5
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


@router.get("/basic", response_model=StatsResponse)
async def get_basic_stats(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get basic statistics for user
    If no user_id provided, uses demo user
    """
    try:
        # Get user (demo if not specified)
        if not user_id:
            user = get_demo_user(db)
        else:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

        user_id = user.id

        # 1. Total cards (active cards in target language)
        cards_total = db.query(Card).join(Sentence).join(Word).filter(
            and_(
                Card.is_active == True,
                Word.language_id == user.target_language_id
            )
        ).count()

        # 2. Cards by memory stage
        stage_counts = db.query(
            UserCardState.status,
            func.count(UserCardState.id).label('count')
        ).join(Card).join(Sentence).join(Word).filter(
            and_(
                UserCardState.user_id == user_id,
                Card.is_active == True,
                Word.language_id == user.target_language_id
            )
        ).group_by(UserCardState.status).all()

        # Initialize counts
        new_count = 0
        learning_count = 0
        review_count = 0
        mature_count = 0

        # Map stage counts
        for status, count in stage_counts:
            if status == MemoryStage.NEW:
                new_count = count
            elif status == MemoryStage.LEARNING:
                learning_count = count
            elif status == MemoryStage.REVIEW:
                review_count = count
            elif status == MemoryStage.MATURE:
                mature_count = count

        # 3. Reviews today
        today_start = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)

        reviews_today = db.query(ReviewEvent).filter(
            and_(
                ReviewEvent.user_id == user_id,
                ReviewEvent.created_at >= today_start
            )
        ).count()

        # 4. Accuracy today
        correct_today = db.query(ReviewEvent).filter(
            and_(
                ReviewEvent.user_id == user_id,
                ReviewEvent.created_at >= today_start,
                ReviewEvent.was_correct == True
            )
        ).count()

        accuracy_today = correct_today / max(reviews_today, 1)  # Avoid division by zero

        # 5. New cards today
        # Count cards that had their FIRST review today
        # Simplified approach: find cards seen today but not before today
        cards_seen_today = db.query(
            func.distinct(ReviewEvent.card_id)
        ).filter(
            and_(
                ReviewEvent.user_id == user_id,
                func.date(ReviewEvent.created_at) == func.current_date()
            )
        ).subquery()

        cards_seen_before_today = db.query(
            func.distinct(ReviewEvent.card_id)
        ).filter(
            and_(
                ReviewEvent.user_id == user_id,
                func.date(ReviewEvent.created_at) < func.current_date()
            )
        ).subquery()

        # Cards seen today but never before today
        new_cards_today = db.query(Card.id).filter(
            and_(
                Card.id.in_(cards_seen_today),
                ~Card.id.in_(cards_seen_before_today)
            )
        ).count() or 0

        # 6. Upcoming reviews (next 7 days)
        upcoming_start = utc_today()
        upcoming_end = upcoming_start + timedelta(days=7)

        upcoming_reviews = db.query(
            func.date(UserCardState.next_review_at).label('review_date'),
            func.count(UserCardState.id).label('count')
        ).join(Card).join(Sentence).join(Word).filter(
            and_(
                UserCardState.user_id == user_id,
                Card.is_active == True,
                Word.language_id == user.target_language_id,
                UserCardState.next_review_at.between(upcoming_start, upcoming_end)
            )
        ).group_by(func.date(UserCardState.next_review_at)).all()

        # Convert to dict with date strings
        upcoming_dict = {
            str(review_date): count for review_date, count in upcoming_reviews
        }

        # Fill missing dates with 0
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
            upcoming_reviews=upcoming_dict
        )

    except Exception as e:
        print(f"Error in get_basic_stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """Health check for stats service"""
    return {"status": "healthy", "service": "stats-api"}
