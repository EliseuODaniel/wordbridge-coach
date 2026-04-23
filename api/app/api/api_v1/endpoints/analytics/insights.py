"""Analytics and insights endpoints for WordBridge Coach."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.models import (
    WordTheme, WordThemeMapping,
    UserThemeStats, UserDailyStats, User, ReviewEvent
)
from app.services.insights_service import (
    get_word_insight_by_card_id,
    get_word_insight_by_word_id,
    get_word_theme_names,
)

router = APIRouter()


class WordInsightResponse(BaseModel):
    """Response model for word insights"""
    word_id: str
    word: str
    rank: Optional[int]
    coverage_pct: Optional[float]
    frequency_score: Optional[float]
    band: Optional[int]
    grammar_info: dict
    frequency_description: str
    coverage_description: str


class ThemePerformanceResponse(BaseModel):
    """Response model for theme performance"""
    theme_id: str
    name: str
    attempts: int
    correct: int
    accuracy: float
    avg_response_time_ms: float
    last_practiced_at: Optional[str]
    difficulty_words: List[str]


class UserDailyStatsResponse(BaseModel):
    """Response model for daily statistics"""
    date: str
    cards_answered: int
    new_words_learned: int
    reviews_done: int
    accuracy: float
    cumulative_mastered_words: int


class RecentPerformanceResponse(BaseModel):
    """Response model for recent performance"""
    recent_responses: List[dict]
    metrics: dict


@router.get("/word/{word_id}", response_model=WordInsightResponse)
async def get_word_insights(
    word_id: str,
    db: Session = Depends(get_db)
):
    """Get frequency and grammar information for a word."""
    try:
        return WordInsightResponse(**get_word_insight_by_word_id(db, word_id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/word/{word_id}/themes", response_model=List[str])
async def get_word_themes(
    word_id: str,
    db: Session = Depends(get_db)
):
    """Get all theme names for a word."""
    try:
        return get_word_theme_names(db, word_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/word-by-card/{card_id}", response_model=WordInsightResponse)
async def get_word_insights_by_card(
    card_id: str,
    db: Session = Depends(get_db)
):
    """Get frequency and grammar information for the word in a card."""
    try:
        return WordInsightResponse(**get_word_insight_by_card_id(db, card_id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/user/{user_id}/themes", response_model=List[ThemePerformanceResponse])
async def get_user_theme_performance(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user performance by thematic clusters
    """
    try:
        # Parse UUID
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"error": "Invalid user ID format", "message": "User ID must be a valid UUID"}
            )

        # Verify user exists
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail={"error": "User not found", "message": f"User with ID {user_id} not found"}
            )

        # Get theme statistics with theme names
        theme_stats = db.query(UserThemeStats, WordTheme).join(
            WordTheme, UserThemeStats.theme_id == WordTheme.id
        ).filter(
            UserThemeStats.user_id == user_uuid,
            WordTheme.is_active == True
        ).all()

        result = []
        for user_stat, theme in theme_stats:
            # Get difficulty words for this theme
            difficulty_words = _get_difficulty_words_for_theme(db, user_uuid, theme.id)

            result.append({
                "theme_id": str(theme.id),
                "name": theme.name,
                "attempts": user_stat.attempts,
                "correct": user_stat.correct,
                "accuracy": user_stat.accuracy,
                "avg_response_time_ms": user_stat.avg_response_time_ms,
                "last_practiced_at": user_stat.last_practiced_at.isoformat() if user_stat.last_practiced_at else None,
                "difficulty_words": difficulty_words
            })

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/user/{user_id}/daily")
async def get_user_daily_progress(
    user_id: str,
    days: Optional[int] = Query(30, description="Number of days to include"),
    db: Session = Depends(get_db)
):
    """
    Get user daily progress and trends
    """
    try:
        # Parse UUID
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"error": "Invalid user ID format", "message": "User ID must be a valid UUID"}
            )

        # Verify user exists
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail={"error": "User not found", "message": f"User with ID {user_id} not found"}
            )

        # Calculate date range using UTC for consistency with tests
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days - 1)

        # Get daily statistics
        daily_stats = db.query(UserDailyStats).filter(
            UserDailyStats.user_id == user_uuid,
            UserDailyStats.date >= start_date,
            UserDailyStats.date <= end_date
        ).order_by(UserDailyStats.date).all()

        # Build response
        daily_data = []
        for stat in daily_stats:
            daily_data.append({
                "date": stat.date.isoformat(),
                "cards_answered": stat.cards_answered,
                "new_words_learned": stat.new_words_learned,
                "reviews_done": stat.reviews_done,
                "accuracy": stat.accuracy,
                "cumulative_mastered_words": stat.cumulative_mastered_words
            })

        # Calculate summary
        if daily_data:
            total_days = len(daily_data)
            avg_daily_cards = sum(d["cards_answered"] for d in daily_data) / total_days
            avg_accuracy = sum(d["accuracy"] for d in daily_data) / total_days
            total_new_words = sum(d["new_words_learned"] for d in daily_data)
            vocabulary_growth = daily_data[-1]["cumulative_mastered_words"] if daily_data else 0
        else:
            total_days = 0
            avg_daily_cards = 0
            avg_accuracy = 0
            total_new_words = 0
            vocabulary_growth = 0

        return {
            "daily_stats": daily_data,
            "summary": {
                "total_days": total_days,
                "avg_daily_cards": round(avg_daily_cards, 1),
                "avg_accuracy": round(avg_accuracy, 3),
                "total_new_words": total_new_words,
                "vocabulary_growth": vocabulary_growth
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/user/{user_id}/recent", response_model=RecentPerformanceResponse)
async def get_recent_performance(
    user_id: str,
    responses: Optional[int] = Query(30, description="Number of recent responses to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get recent performance metrics
    """
    try:
        # Parse UUID
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={"error": "Invalid user ID format", "message": "User ID must be a valid UUID"}
            )

        # Verify user exists
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HTTPException(
                status_code=404,
                detail={"error": "User not found", "message": f"User with ID {user_id} not found"}
            )

        # Get recent review events
        recent_events = db.query(ReviewEvent).filter(
            ReviewEvent.user_id == user_uuid
        ).order_by(ReviewEvent.created_at.desc()).limit(responses).all()

        # Build recent responses data
        recent_responses = []
        for event in recent_events:
            recent_responses.append({
                "card_id": str(event.card_id),
                "word": "word_placeholder",  # Would need to join with Card/Word
                "was_correct": event.was_correct,
                "response_time_ms": event.response_time_ms,
                "quality": event.quality,
                "timestamp": event.created_at.isoformat()
            })

        # Calculate metrics
        if recent_responses:
            correct_count = sum(1 for r in recent_responses if r["was_correct"])
            accuracy_recent = correct_count / len(recent_responses)
            avg_response_time = sum(r["response_time_ms"] for r in recent_responses) / len(recent_responses)

            # Determine trend direction (simple implementation)
            if len(recent_responses) >= 10:
                first_half = recent_responses[len(recent_responses)//2:]
                second_half = recent_responses[:len(recent_responses)//2]

                first_half_accuracy = sum(1 for r in first_half if r["was_correct"]) / len(first_half)
                second_half_accuracy = sum(1 for r in second_half if r["was_correct"]) / len(second_half)

                if second_half_accuracy > first_half_accuracy:
                    trend_direction = "improving"
                elif second_half_accuracy < first_half_accuracy:
                    trend_direction = "declining"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "insufficient_data"
        else:
            accuracy_recent = 0.0
            avg_response_time = 0.0
            trend_direction = "no_data"

        return {
            "recent_responses": recent_responses,
            "metrics": {
                "accuracy_recent": round(accuracy_recent, 3),
                "avg_response_time_ms": round(avg_response_time, 1),
                "trend_direction": trend_direction,
                "session_cards": len(recent_responses)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)}
        )


def _get_difficulty_words_for_theme(db: Session, user_id: str, theme_id: str, limit: int = 3) -> List[str]:
    """Return placeholder difficult words until theme difficulty ranking is extracted to a service."""
    return []
