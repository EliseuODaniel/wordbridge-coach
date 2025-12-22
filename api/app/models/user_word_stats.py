"""User word statistics model for tracking individual word performance"""

from sqlalchemy import Column, Integer, Float, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import uuid


class UserWordStats(BaseModel):
    """Track user performance on individual words"""

    __tablename__ = "user_word_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    word_id = Column(UUID(as_uuid=True), ForeignKey("word.id"), nullable=False)

    # Performance metrics
    total_attempts = Column(Integer, default=0, nullable=False)
    correct_attempts = Column(Integer, default=0, nullable=False)
    accuracy_rate = Column(Float, default=0.0, nullable=False)

    # Mastery and difficulty tracking
    mastery_score = Column(Float, default=0.0, nullable=False, comment="0.0 = new, 1.0 = mastered")
    last_result = Column(Boolean, nullable=True, comment="Result of last attempt")
    consecutive_correct = Column(Integer, default=0, nullable=False)
    consecutive_incorrect = Column(Integer, default=0, nullable=False)

    # Timing
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    first_attempt_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="word_stats")
    word = relationship("Word", back_populates="user_stats")

    # Indexes
    __table_args__ = (
        Index('idx_user_word_stats_user_word', 'user_id', 'word_id', unique=True),
        Index('idx_user_word_stats_user_mastery', 'user_id', 'mastery_score'),
        Index('idx_user_word_stats_user_accuracy', 'user_id', 'accuracy_rate'),
    )

    def __repr__(self):
        return f"<UserWordStats(user_id={self.user_id}, word_id={self.word_id}, mastery={self.mastery_score:.2f})>"

    @property
    def is_struggling(self) -> bool:
        """Word needs more practice if accuracy < 0.6 or mastery < 0.3"""
        return self.accuracy_rate < 0.6 or self.mastery_score < 0.3

    @property
    def is_mature(self) -> bool:
        """Word is well-known if accuracy > 0.8 and mastery > 0.7"""
        return self.accuracy_rate > 0.8 and self.mastery_score > 0.7

    def update_stats(self, correct: bool):
        """Update statistics after a new attempt"""
        from datetime import datetime, timezone

        self.total_attempts += 1
        if correct:
            self.correct_attempts += 1
            self.consecutive_correct += 1
            self.consecutive_incorrect = 0
        else:
            self.consecutive_incorrect += 1
            self.consecutive_correct = 0

        self.last_result = correct
        self.last_attempt_at = datetime.now(timezone.utc)

        if self.first_attempt_at is None:
            self.first_attempt_at = self.last_attempt_at

        # Update accuracy rate
        self.accuracy_rate = self.correct_attempts / self.total_attempts

        # Update mastery score based on performance
        self._update_mastery_score()

    def _update_mastery_score(self):
        """Update mastery score using exponential moving average"""
        # Base mastery update rate
        alpha = 0.3

        # Recent performance weight
        if self.last_result is not None:
            recent_weight = 0.5 if self.consecutive_correct > 2 else 0.3
            if self.consecutive_incorrect > 2:
                recent_weight = 0.1

            # Update mastery with weighted average
            target_mastery = 1.0 if self.last_result else 0.0
            self.mastery_score = (1 - alpha) * self.mastery_score + alpha * recent_weight * target_mastery
        else:
            # Decay mastery slightly over time without recent attempts
            self.mastery_score *= 0.95