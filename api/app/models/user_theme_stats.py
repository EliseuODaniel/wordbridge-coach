"""User theme statistics model for FillTheWord analytics"""

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.core.time import utc_now
import uuid


class UserThemeStats(BaseModel):
    """Aggregated performance statistics per user per theme"""

    __tablename__ = "user_theme_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False, comment="User ID")
    theme_id = Column(UUID(as_uuid=True), ForeignKey('word_themes.id'), nullable=False, comment="Theme ID")
    attempts = Column(Integer, default=0, nullable=False, comment="Total number of attempts")
    correct = Column(Integer, default=0, nullable=False, comment="Number of correct attempts")
    accuracy = Column(Float, default=0.0, nullable=False, comment="Accuracy rate (correct / attempts)")
    avg_response_time_ms = Column(Float, default=0.0, nullable=False, comment="Average response time in milliseconds")
    last_practiced_at = Column(DateTime, nullable=True, comment="Last practice timestamp")
    created_at = Column(DateTime, default=utc_now, comment="Creation timestamp")
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, comment="Update timestamp")

    # Relationships
    user = relationship("User", back_populates="theme_stats")
    theme = relationship("WordTheme", back_populates="user_stats")

    # Indexes for performance
    __table_args__ = (
        Index('idx_user_theme_stats_user', 'user_id'),
        Index('idx_user_theme_stats_theme', 'theme_id'),
        Index('idx_user_theme_stats_user_theme', 'user_id', 'theme_id', unique=True),
        Index('idx_user_theme_stats_last_practiced', 'last_practiced_at'),
        Index('idx_user_theme_stats_accuracy', 'accuracy'),
    )

    def update_accuracy(self):
        """Update accuracy based on current attempts and correct"""
        if self.attempts > 0:
            self.accuracy = self.correct / self.attempts
        else:
            self.accuracy = 0.0

    def add_attempt(self, was_correct: bool, response_time_ms: float):
        """Add a new attempt and update statistics"""
        self.attempts += 1
        if was_correct:
            self.correct += 1
        self.update_accuracy()

        # Update average response time using incremental formula
        if self.attempts == 1:
            self.avg_response_time_ms = response_time_ms
        else:
            # Incremental average: new_avg = (old_avg * (n-1) + new_value) / n
            self.avg_response_time_ms = (
                (self.avg_response_time_ms * (self.attempts - 1) + response_time_ms) / self.attempts
            )

        self.last_practiced_at = utc_now()

    def __repr__(self):
        return f"<UserThemeStats(user_id='{self.user_id}', theme_id='{self.theme_id}', accuracy={self.accuracy:.3f})>"
