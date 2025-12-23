"""Settings endpoints for FillTheWord"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.models import User
from pydantic import BaseModel, Field

router = APIRouter()


class SettingsResponse(BaseModel):
    """Response model for user settings"""
    daily_new_limit: int = Field(..., ge=5, le=20, description="Daily new cards limit (5-20)")
    easiness_factor: float = Field(..., ge=1.3, le=2.5, description="SM-2 easiness factor (1.3-2.5)")
    word_goal_rank: int = Field(..., ge=100, le=10000, description="Word frequency goal rank (100, 500, 1000, 1500, 3000, 5000, 10000)")


class SettingsUpdate(BaseModel):
    """Request model for updating settings"""
    daily_new_limit: Optional[int] = Field(None, ge=5, le=20, description="Daily new cards limit (5-20)")
    easiness_factor: Optional[float] = Field(None, ge=1.3, le=2.5, description="SM-2 easiness factor (1.3-2.5)")


def get_demo_user(db: Session) -> User:
    """Get or create demo user"""
    user = db.query(User).filter(User.username == "demo").first()
    if not user:
        # Create demo user if not exists - reuse logic from stats
        from app.models import Language

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


@router.get("/", response_model=SettingsResponse)
async def get_settings(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get user settings
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

        return SettingsResponse(
            daily_new_limit=user.daily_new_limit,
            easiness_factor=user.easiness_factor,
            word_goal_rank=user.word_goal_rank
        )

    except Exception as e:
        print(f"Error in get_settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/", response_model=SettingsResponse)
async def update_settings(
    settings_update: SettingsUpdate,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update user settings
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

        # Update settings if provided
        if settings_update.daily_new_limit is not None:
            user.daily_new_limit = settings_update.daily_new_limit

        if settings_update.easiness_factor is not None:
            user.easiness_factor = settings_update.easiness_factor

        db.commit()
        db.refresh(user)

        return SettingsResponse(
            daily_new_limit=user.daily_new_limit,
            easiness_factor=user.easiness_factor,
            word_goal_rank=user.word_goal_rank
        )

    except Exception as e:
        print(f"Error in update_settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def health_check():
    """Health check for settings service"""
    return {"status": "healthy", "service": "settings-api"}