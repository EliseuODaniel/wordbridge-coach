"""User daily statistics model for WordBridge Coach analytics."""

from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.core.time import utc_now
import uuid
from datetime import date


class UserDailyStats(BaseModel):
    """Daily aggregated learning metrics per user"""

    __tablename__ = "user_daily_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False, comment="User ID")
    date = Column(Date, nullable=False, comment="Statistics date")
    cards_answered = Column(Integer, default=0, nullable=False, comment="Number of cards answered")
    new_words_learned = Column(Integer, default=0, nullable=False, comment="New words that passed mastery threshold")
    reviews_done = Column(Integer, default=0, nullable=False, comment="Number of review attempts")
    accuracy = Column(Float, default=0.0, nullable=False, comment="Daily accuracy rate")
    cumulative_mastered_words = Column(Integer, default=0, nullable=False, comment="Total mastered words up to this date")
    created_at = Column(DateTime, default=utc_now, comment="Creation timestamp")
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, comment="Update timestamp")

    # Relationships
    user = relationship("User", back_populates="daily_stats")

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_daily_stats_user', 'user_id'),
        Index('idx_user_daily_stats_date', 'date'),
        Index('idx_user_daily_stats_user_date', 'user_id', 'date', unique=True),
        Index('idx_user_daily_stats_cards_answered', 'cards_answered'),
        Index('idx_user_daily_stats_accuracy', 'accuracy'),
        Index('idx_user_daily_stats_cumulative_mastered', 'cumulative_mastered_words'),
    )

    def update_accuracy(self, was_correct: bool):
        """Update accuracy based on new attempt"""
        self.reviews_done += 1
        if was_correct:
            self.cards_answered += 1

        # Calculate accuracy rate
        if self.reviews_done > 0:
            self.accuracy = self.cards_answered / self.reviews_done
        else:
            self.accuracy = 0.0

    def add_new_word(self):
        """Increment new words learned counter"""
        self.new_words_learned += 1
        self.cumulative_mastered_words += 1

    def __repr__(self):
        return f"<UserDailyStats(user_id='{self.user_id}', date='{self.date}', accuracy={self.accuracy:.3f})>"
