"""User management endpoints for FillTheWord"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.models import User, Language, Card, UserCardState, UserWordStats, MemoryStage, Sentence, Word, ReviewEvent

router = APIRouter()


class UserResponse(BaseModel):
    """Response model for user data"""
    id: str
    username: str
    language_preference: str
    created_at: str


class CreateUserRequest(BaseModel):
    """Request model for creating a user"""
    username: str
    language_preference: str = "pt"  # Native/interface language
    target_language: str = "en"    # Target language for learning (en or fr)
    word_goal_rank: int = 1000     # Goal: 100, 500, 1500, 3000, 5000, 10000


class UpdateUserRequest(BaseModel):
    """Request model for updating a user"""
    username: Optional[str] = None
    language_preference: Optional[str] = None  # Native/interface language
    target_language: Optional[str] = None     # Target language for learning (en or fr)
    word_goal_rank: Optional[int] = None      # Spec4: Vocabulary goal {100, 500, 1500, 3000, 5000, 10000}


@router.get("/", response_model=List[UserResponse])
async def list_users(db: Session = Depends(get_db)):
    """
    List all users
    """
    try:
        users = db.query(User).all()
        return [
            {
                "id": str(user.id),
                "username": user.username,
                "language_preference": user.language_preference,
                "created_at": user.created_at.isoformat()
            }
            for user in users
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: CreateUserRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new user
    """
    try:
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Username already taken", "message": f"Username '{user_data.username}' is already taken"}
            )

        # Get target language (learning target: en or fr)
        target_lang = db.query(Language).filter(Language.code == user_data.target_language).first()
        if not target_lang:
            target_lang = db.query(Language).filter(Language.code == "en").first()
            if not target_lang:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Target language not found", "message": f"Target language '{user_data.target_language}' not configured"}
                )

        # Get native language (interface language: pt, es, fr, en)
        native_lang = db.query(Language).filter(Language.code == user_data.language_preference).first()
        if not native_lang:
            native_lang = db.query(Language).filter(Language.code == "pt").first()
            if not native_lang:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={"error": "Native language not found", "message": f"Native language '{user_data.language_preference}' not configured"}
                )

        # Create new user
        new_user = User(
            id=str(uuid.uuid4()),
            username=user_data.username,
            language_preference=user_data.language_preference,
            native_language_id=native_lang.id,
            target_language_id=target_lang.id,
            daily_new_limit=10,
            easiness_factor=2.5,
            word_goal_rank=user_data.word_goal_rank  # ← Campo crítico adicionado!
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Initialize UserCardState for Band 1 cards for new users
        initialize_user_card_states(db, new_user.id, target_lang.id)

        return {
            "id": str(new_user.id),
            "username": new_user.username,
            "language_preference": new_user.language_preference,
            "created_at": new_user.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


def initialize_user_card_states(db: Session, user_id: str, target_language_id: str):
    """
    Initialize UserCardState for Band 1 cards for new users.
    This ensures new users have cards available immediately after account creation.
    """
    try:
        from sqlalchemy import and_
        from datetime import datetime

        # Get active cards from Band 1 (ranks 1-1000) for the target language
        band_1_cards = db.query(Card).join(Sentence).join(Word).filter(
            and_(
                Card.is_active == True,
                Sentence.language_id == target_language_id,
                Word.frequency_rank.isnot(None),
                Word.frequency_rank <= 1000  # Band 1
            )
        ).limit(50).all()  # Start with 50 cards to avoid overwhelming

        if not band_1_cards:
            print(f"Warning: No Band 1 cards found for language {target_language_id}")
            return

        # Create UserCardState for each card
        new_states = []
        for card in band_1_cards:
            # Check if UserCardState already exists
            existing_state = db.query(UserCardState).filter(
                and_(
                    UserCardState.user_id == user_id,
                    UserCardState.card_id == card.id
                )
            ).first()

            if not existing_state:
                new_state = UserCardState(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    card_id=card.id,
                    status=MemoryStage.NEW,
                    easiness_factor=2.5,
                    interval_days=1,
                    repetitions=0,
                    next_review_at=datetime.utcnow()
                )
                new_states.append(new_state)

        if new_states:
            db.bulk_save_objects(new_states)
            db.commit()
            print(f"Initialized {len(new_states)} UserCardState records for new user {user_id}")

    except Exception as e:
        print(f"Error initializing UserCardState for user {user_id}: {e}")
        db.rollback()
        # Don't raise exception - user creation should still succeed
        pass


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user by ID
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "User not found", "message": f"User with ID {user_id} not found"}
            )

        return {
            "id": str(user.id),
            "username": user.username,
            "language_preference": user.language_preference,
            "created_at": user.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UpdateUserRequest,
    db: Session = Depends(get_db)
):
    """
    Update a user
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "User not found", "message": f"User with ID {user_id} not found"}
            )

        # Track if target_language is being changed
        target_language_changed = False
        old_target_language_id = user.target_language_id

        # Update fields if provided
        if user_data.username is not None:
            # Check if username already exists (excluding current user)
            existing_user = db.query(User).filter(
                User.username == user_data.username,
                User.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": "Username already exists", "message": f"Username '{user_data.username}' is already taken"}
                )
            user.username = user_data.username

        if user_data.language_preference is not None:
            # Validate and set native language
            native_lang = db.query(Language).filter(Language.code == user_data.language_preference).first()
            if not native_lang:
                native_lang = db.query(Language).filter(Language.code == "pt").first()
                if not native_lang:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail={"error": "Native language not found", "message": f"Native language '{user_data.language_preference}' not configured"}
                    )
            user.language_preference = user_data.language_preference
            user.native_language_id = native_lang.id

        if user_data.target_language is not None:
            # Validate and set target language
            target_lang = db.query(Language).filter(Language.code == user_data.target_language).first()
            if not target_lang:
                target_lang = db.query(Language).filter(Language.code == "en").first()
                if not target_lang:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail={"error": "Target language not found", "message": f"Target language '{user_data.target_language}' not configured"}
                    )

            # Check if target language is actually changing
            if user.target_language_id != target_lang.id:
                target_language_changed = True
                old_target_language_id = user.target_language_id
                user.target_language_id = target_lang.id

        # Spec4: Update word_goal_rank if provided
        if user_data.word_goal_rank is not None:
            # Validate against allowed values
            ALLOWED_GOALS = {100, 500, 1500, 3000, 5000, 10000}
            if user_data.word_goal_rank not in ALLOWED_GOALS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Invalid word_goal_rank",
                        "message": f"word_goal_rank must be one of: {sorted(ALLOWED_GOALS)}"
                    }
                )

            # Update user goal
            user.word_goal_rank = user_data.word_goal_rank

            # Update UserFrequencyProgress if exists
            from app.models.user_frequency_progress import UserFrequencyProgress
            progress = db.query(UserFrequencyProgress).filter(
                UserFrequencyProgress.user_id == user_id
            ).first()

            if progress:
                # Clamp current_window_end_rank to new goal
                progress.word_goal_rank = user_data.word_goal_rank
                progress.current_window_end_rank = min(
                    progress.current_window_end_rank,
                    user_data.word_goal_rank
                )
                # Note: we DON'T clamp max_contiguous_mastered_rank as that represents actual progress
                print(f"DEBUG: Updated UserFrequencyProgress for user {user_id} to goal {user_data.word_goal_rank}")

        db.commit()
        db.refresh(user)

        # If target language changed, reset user progress for new language
        if target_language_changed:
            print(f"Target language changed for user {user_id}, resetting progress for new language")
            # Remove existing UserCardState records for old language
            db.query(UserCardState).filter(UserCardState.user_id == user_id).delete()
            # Remove existing UserWordStats records for old language
            db.query(UserWordStats).filter(UserWordStats.user_id == user_id).delete()
            db.commit()
            # Initialize new cards for the new target language
            initialize_user_card_states(db, user_id, user.target_language_id)

        return {
            "id": str(user.id),
            "username": user.username,
            "language_preference": user.language_preference,
            "created_at": user.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a user and their associated data
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "User not found", "message": f"User with ID {user_id} not found"}
            )

        # Delete related data in correct order to respect foreign key constraints

        # Delete UserCardState records
        deleted_card_states = db.query(UserCardState).filter(UserCardState.user_id == user_id).delete()

        # Delete UserWordStats records
        deleted_word_stats = db.query(UserWordStats).filter(UserWordStats.user_id == user_id).delete()

        # Delete ReviewEvent records
        deleted_review_events = db.query(ReviewEvent).filter(ReviewEvent.user_id == user_id).delete()

        # Finally delete the user
        db.delete(user)
        db.commit()

        return {
            "message": "User deleted successfully",
            "deleted_records": {
                "user": 1,
                "card_states": deleted_card_states,
                "word_stats": deleted_word_stats,
                "review_events": deleted_review_events
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )