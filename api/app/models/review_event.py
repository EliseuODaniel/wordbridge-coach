"""ReviewEvent model for tracking individual reviews"""

from sqlalchemy import Column, Integer, Float, ForeignKey, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ReviewEvent(BaseModel):
    """Individual review session for analytics and SM-2 adjustments"""

    __tablename__ = "reviewevent"

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    card_id = Column(UUID(as_uuid=True), ForeignKey("card.id"), nullable=False)
    sentence_id = Column(UUID(as_uuid=True), ForeignKey("sentence.id"), nullable=True)  # Which sentence was used
    quality = Column(Integer, nullable=False)  # SM-2 quality 0-5
    response_time_ms = Column(Integer, nullable=False)
    user_answer = Column(String(200), nullable=False)
    correct_answer = Column(String(200), nullable=False)
    was_correct = Column(Boolean, nullable=False)
    hints_used = Column(Integer, default=0, nullable=False)
    attempts = Column(Integer, default=1, nullable=False)

    # Lingvist mode fields (nullable to not break Spec4)
    typed_answer = Column(String(200), nullable=True)  # User's typed answer in Lingvist mode
    hints_used_lingvist = Column(JSON, nullable=True)  # Progressive hints used (e.g., {"grammar_tag": true, "first_letter": true})
    attempt_index = Column(Integer, nullable=True)  # Attempt number (1st, 2nd, 3rd...)

    previous_easiness = Column(Float, nullable=True)
    new_easiness = Column(Float, nullable=True)
    previous_interval = Column(Integer, nullable=True)
    new_interval = Column(Integer, nullable=True)
    session_id = Column(UUID(as_uuid=True), nullable=True)  # Study session ID
    
    # Relationships - Temporarily disabled to fix seed
    user = relationship("User", back_populates="review_events")
    card = relationship("Card", back_populates="review_events")
    # user_card_state = relationship("UserCardState", back_populates="review_events")
