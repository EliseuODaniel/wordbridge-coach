"""UserFrequencyProgress model for tracking vocabulary progression"""

from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class UserFrequencyProgress(BaseModel):
    """Track user's vocabulary learning progress by frequency rank"""

    __tablename__ = "user_frequency_progress"

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, unique=True)

    # Until which rank this user wants to reach (100, 500, 1500, 3000, 5000, 10000)
    word_goal_rank = Column(Integer, nullable=False, default=1000)

    # End of current window of eligible "new" words
    current_window_end_rank = Column(Integer, nullable=False, default=100)

    # Highest rank such that ALL words 1..rank had at least 1 correct answer
    max_contiguous_mastered_rank = Column(Integer, nullable=False, default=0)

    # Relationships
    user = relationship("User", back_populates="frequency_progress")

    # Ensure one progress record per user
    __table_args__ = (
        {"schema": None},
    )