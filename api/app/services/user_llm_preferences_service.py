"""
User LLM Preferences Service

Handles CRUD operations for user LLM model preferences in Chat Coach.
"""

import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user_llm_preferences import UserLLMPreferences
from app.llm.profiles import get_default_chat_profile, get_default_teacher_profile, validate_profile_id


def _normalize_preferences(db: Session, preferences: UserLLMPreferences) -> UserLLMPreferences:
    """Coerce stale or removed profile ids back to supported defaults."""
    changed = False

    if not validate_profile_id(preferences.chat_model_profile):
        preferences.chat_model_profile = get_default_chat_profile()
        changed = True

    if not validate_profile_id(preferences.teacher_model_profile):
        preferences.teacher_model_profile = get_default_teacher_profile()
        changed = True

    if changed:
        db.commit()
        db.refresh(preferences)

    return preferences


def get_user_llm_preferences(db: Session, user_id: uuid.UUID) -> UserLLMPreferences:
    """
    Get user's LLM preferences, creating defaults if not exist.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        UserLLMPreferences object (created if not exists)
    """
    # Try to fetch existing preferences
    stmt = select(UserLLMPreferences).where(UserLLMPreferences.user_id == user_id)
    result = db.execute(stmt).scalar_one_or_none()

    if result is None:
        # Create default preferences for user
        preferences = UserLLMPreferences(
            user_id=user_id,
            chat_model_profile=get_default_chat_profile(),
            teacher_model_profile=get_default_teacher_profile()
        )
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
        return preferences

    return _normalize_preferences(db, result)


def update_user_llm_preferences(
    db: Session,
    user_id: uuid.UUID,
    chat_model_profile: Optional[str] = None,
    teacher_model_profile: Optional[str] = None
) -> UserLLMPreferences:
    """
    Update user's LLM preferences.

    Args:
        db: Database session
        user_id: User UUID
        chat_model_profile: New chat profile ID (optional)
        teacher_model_profile: New teacher profile ID (optional)

    Returns:
        Updated UserLLMPreferences object

    Raises:
        ValueError: If profile_id is invalid
    """
    # Validate profile IDs if provided
    if chat_model_profile is not None and not validate_profile_id(chat_model_profile):
        raise ValueError(f"Invalid chat_model_profile: {chat_model_profile}")

    if teacher_model_profile is not None and not validate_profile_id(teacher_model_profile):
        raise ValueError(f"Invalid teacher_model_profile: {teacher_model_profile}")

    # Get or create preferences
    preferences = get_user_llm_preferences(db, user_id)

    # Update fields if provided
    if chat_model_profile is not None:
        preferences.chat_model_profile = chat_model_profile

    if teacher_model_profile is not None:
        preferences.teacher_model_profile = teacher_model_profile

    db.commit()
    db.refresh(preferences)

    return preferences


def reset_user_llm_preferences(db: Session, user_id: uuid.UUID) -> UserLLMPreferences:
    """
    Reset user's LLM preferences to defaults.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        UserLLMPreferences object with defaults
    """
    preferences = get_user_llm_preferences(db, user_id)
    preferences.chat_model_profile = get_default_chat_profile()
    preferences.teacher_model_profile = get_default_teacher_profile()

    db.commit()
    db.refresh(preferences)

    return preferences


def get_user_model_profiles(db: Session, user_id: uuid.UUID) -> Dict[str, str]:
    """
    Get user's selected model profiles for chat and teacher.

    Convenience function for use in chat.py WebSocket handler.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        Dict with keys: 'chat_model_profile', 'teacher_model_profile'
    """
    preferences = get_user_llm_preferences(db, user_id)
    return {
        "chat_model_profile": preferences.chat_model_profile,
        "teacher_model_profile": preferences.teacher_model_profile
    }
