#!/usr/bin/env python3
"""
Initialize Spec4 progression for existing users
Creates UserFrequencyProgress records for all existing users
"""

from app.core.database import SessionLocal
from app.models import User, UserFrequencyProgress


def initialize_spec4_progress():
    """Initialize UserFrequencyProgress for all existing users"""

    db = SessionLocal()
    try:
        # Get all users who don't have frequency progress yet
        users_without_progress = db.query(User).outerjoin(UserFrequencyProgress).filter(
            UserFrequencyProgress.user_id.is_(None)
        ).all()

        print(f"Found {len(users_without_progress)} users without Spec4 progress")

        initialized_count = 0
        for user in users_without_progress:
            # Create UserFrequencyProgress with default values
            progress = UserFrequencyProgress(
                user_id=user.id,
                word_goal_rank=user.word_goal_rank,  # Use existing word_goal_rank or default
                current_window_end_rank=min(100, user.word_goal_rank),
                max_contiguous_mastered_rank=0
            )
            db.add(progress)
            initialized_count += 1

            print(f"Initialized progress for user: {user.username} (goal: {user.word_goal_rank})")

        db.commit()
        print(f"Successfully initialized Spec4 progress for {initialized_count} users")

        return True

    except Exception as e:
        print(f"Error initializing Spec4 progress: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = initialize_spec4_progress()
    if success:
        print("Spec4 progress initialization completed successfully!")
    else:
        print("Failed to initialize Spec4 progress")