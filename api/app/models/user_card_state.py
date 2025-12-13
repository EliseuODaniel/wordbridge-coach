"""UserCardState model for SRS SM-2 algorithm"""

from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class MemoryStage(enum.Enum):
    NEW = "new"
    LEARNING = "learning"
    REVIEW = "review"
    RELEARN = "relearn"
    MATURE = "mature"


class UserCardState(BaseModel):
    """Individual card state for each user with SM-2 algorithm"""

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    card_id = Column(UUID(as_uuid=True), ForeignKey("card.id"), nullable=False)
    repetitions = Column(Integer, default=0, nullable=False)  # Correct repetitions
    easiness_factor = Column(Float, default=2.5, nullable=False)  # SM-2 easiness factor
    interval_days = Column(Integer, default=1, nullable=False)  # Interval in days
    next_review_at = Column(DateTime, nullable=False)  # Next review time
    last_reviewed_at = Column(DateTime, nullable=True)  # Last review time
    status = Column(Enum(MemoryStage), default=MemoryStage.NEW, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    correct_reviews = Column(Integer, default=0, nullable=False)
    
    # Relationships - Temporarily disabled to fix seed
    user = relationship("User", back_populates="card_states")
    card = relationship("Card", back_populates="user_states")
    # review_events = relationship("ReviewEvent", back_populates="user_card_state")
    
    @property
    def success_rate(self):
        """Calculate success rate"""
        if self.total_reviews == 0:
            return 0.0
        return round((self.correct_reviews / self.total_reviews) * 100, 1)
    
    @property
    def memory_stage_display(self):
        """Get display representation for frontend"""
        stage_mapping = {
            MemoryStage.NEW: 0,        # 0 bolinhas (cinza)
            MemoryStage.LEARNING: 1,   # 1-2 bolinhas (amarelo)
            MemoryStage.REVIEW: 3,     # 3 bolinhas (azul)
            MemoryStage.RELEARN: 1,    # 1-2 bolinhas (amarelo)
            MemoryStage.MATURE: 4,     # 4 bolinhas (verde)
        }
        return stage_mapping.get(self.status, 0)
