"""
LLM Profile Management Endpoints

Provides API endpoints for:
1. Listing available LLM profiles
2. Getting user's LLM preferences
3. Updating user's LLM preferences
"""

import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.llm_profiles import (
    LLMProfileListResponse,
    LLMProfileResponse,
    UserLLMPreferencesResponse,
    UserLLMPreferencesUpdate
)
from app.llm.profiles import list_profiles, get_profile
from app.services.user_llm_preferences_service import (
    get_user_llm_preferences,
    update_user_llm_preferences
)


logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# LLM Profile Endpoints
# ============================================================================

@router.get("/llm-profiles", response_model=LLMProfileListResponse)
async def get_available_llm_profiles(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all available LLM profiles.

    Returns catalog of models that can be selected for chat or teacher analysis.
    """
    profiles = list_profiles()

    # Convert LLMProfile objects to dicts for Pydantic serialization
    profiles_data = [profile.model_dump() for profile in profiles]

    logger.info(f"[LLM_PROFILES] Listed {len(profiles)} available profiles for user_id={user_id}")

    return LLMProfileListResponse(profiles=profiles_data)


@router.get("/llm-profiles/{profile_id}", response_model=LLMProfileResponse)
async def get_llm_profile(
    profile_id: str,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific LLM profile.
    """
    try:
        profile = get_profile(profile_id)
        logger.info(f"[LLM_PROFILES] Retrieved profile {profile_id} for user_id={user_id}")
        return profile.model_dump()
    except ValueError as e:
        logger.warning(f"[LLM_PROFILES] Invalid profile requested: {profile_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile not found: {profile_id}"
        )


# ============================================================================
# User LLM Preferences Endpoints
# ============================================================================

@router.get("/users/me/llm-preferences", response_model=UserLLMPreferencesResponse)
async def get_my_llm_preferences(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get current user's LLM preferences.

    Returns the selected models for chat and teacher analysis.
    If user has no preferences set, returns defaults (qwen2.5-7b-instruct for both).
    """
    # Convert user_id string to UUID
    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            logger.warning(f"[LLM_PREFS] Invalid user_id format: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user_id format"
            )
    else:
        # Demo user fallback
        user_uuid = uuid.UUID("dceadc65-5f92-4e0c-8422-c7013a69ba18")

    preferences = get_user_llm_preferences(db, user_uuid)

    logger.info(f"[LLM_PREFS] Retrieved preferences for user_id={user_id}: "
                f"chat={preferences.chat_model_profile}, "
                f"teacher={preferences.teacher_model_profile}")

    return UserLLMPreferencesResponse(
        id=str(preferences.id),
        user_id=str(preferences.user_id),
        chat_model_profile=preferences.chat_model_profile,
        teacher_model_profile=preferences.teacher_model_profile,
        created_at=preferences.created_at,
        updated_at=preferences.updated_at
    )


@router.put("/users/me/llm-preferences", response_model=UserLLMPreferencesResponse)
async def update_my_llm_preferences(
    update_data: UserLLMPreferencesUpdate,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update current user's LLM preferences.

    Allows changing the selected models for chat and teacher analysis.
    Only updates fields that are provided (null = no change).

    Validates that profile IDs exist before updating.
    """
    # Convert user_id string to UUID
    if user_id:
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            logger.warning(f"[LLM_PREFS] Invalid user_id format: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user_id format"
            )
    else:
        # Demo user fallback
        user_uuid = uuid.UUID("dceadc65-5f92-4e0c-8422-c7013a69ba18")

    # Extract fields
    chat_profile = update_data.chat_model_profile
    teacher_profile = update_data.teacher_model_profile

    # Both null is a no-op
    if chat_profile is None and teacher_profile is None:
        logger.info(f"[LLM_PREFS] No-op update for user_id={user_id} (both fields null)")
        preferences = get_user_llm_preferences(db, user_uuid)
        return UserLLMPreferencesResponse(
            id=str(preferences.id),
            user_id=str(preferences.user_id),
            chat_model_profile=preferences.chat_model_profile,
            teacher_model_profile=preferences.teacher_model_profile,
            created_at=preferences.created_at,
            updated_at=preferences.updated_at
        )

    try:
        preferences = update_user_llm_preferences(
            db,
            user_uuid,
            chat_model_profile=chat_profile,
            teacher_model_profile=teacher_profile
        )

        logger.info(f"[LLM_PREFS] Updated preferences for user_id={user_id}: "
                    f"chat={preferences.chat_model_profile}, "
                    f"teacher={preferences.teacher_model_profile}")

        return UserLLMPreferencesResponse(
            id=str(preferences.id),
            user_id=str(preferences.user_id),
            chat_model_profile=preferences.chat_model_profile,
            teacher_model_profile=preferences.teacher_model_profile,
            created_at=preferences.created_at,
            updated_at=preferences.updated_at
        )

    except ValueError as e:
        logger.warning(f"[LLM_PREFS] Invalid profile update for user_id={user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
