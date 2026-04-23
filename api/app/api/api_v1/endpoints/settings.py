"""Settings endpoints for WordBridge Coach."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.request_user_service import get_request_user

router = APIRouter()


class SettingsResponse(BaseModel):
    """Response model for user settings."""

    daily_new_limit: int = Field(..., ge=5, le=20, description='Daily new cards limit (5-20)')
    easiness_factor: float = Field(..., ge=1.3, le=2.5, description='SM-2 easiness factor (1.3-2.5)')
    word_goal_rank: int = Field(..., ge=100, le=10000, description='Word frequency goal rank (100, 500, 1000, 1500, 3000, 5000, 10000)')


class SettingsUpdate(BaseModel):
    """Request model for updating settings."""

    daily_new_limit: Optional[int] = Field(None, ge=5, le=20, description='Daily new cards limit (5-20)')
    easiness_factor: Optional[float] = Field(None, ge=1.3, le=2.5, description='SM-2 easiness factor (1.3-2.5)')


@router.get('/', response_model=SettingsResponse)
async def get_settings(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get persisted user settings without implicit demo bootstrap."""
    try:
        user = get_request_user(db, user_id)
        return SettingsResponse(
            daily_new_limit=user.daily_new_limit,
            easiness_factor=user.easiness_factor,
            word_goal_rank=user.word_goal_rank,
        )
    except HTTPException:
        raise
    except Exception as exc:
        print(f'Error in get_settings: {exc}')
        raise HTTPException(status_code=500, detail='Internal server error')


@router.patch('/', response_model=SettingsResponse)
async def update_settings(
    settings_update: SettingsUpdate,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update persisted user settings without implicit demo bootstrap."""
    try:
        user = get_request_user(db, user_id)

        if settings_update.daily_new_limit is not None:
            user.daily_new_limit = settings_update.daily_new_limit

        if settings_update.easiness_factor is not None:
            user.easiness_factor = settings_update.easiness_factor

        db.commit()
        db.refresh(user)

        return SettingsResponse(
            daily_new_limit=user.daily_new_limit,
            easiness_factor=user.easiness_factor,
            word_goal_rank=user.word_goal_rank,
        )
    except HTTPException:
        raise
    except Exception as exc:
        print(f'Error in update_settings: {exc}')
        db.rollback()
        raise HTTPException(status_code=500, detail='Internal server error')


@router.get('/health')
async def health_check():
    """Health check for settings service."""
    return {'status': 'healthy', 'service': 'settings-api'}
