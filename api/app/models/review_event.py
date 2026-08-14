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

    mode = Column(String(24), nullable=False, default="spec4")
    task_type = Column(String(40), nullable=False, default="gap_recall")
    modality = Column(String(32), nullable=False, default="reading_writing")
    scaffold_level = Column(String(24), nullable=False, default="independent")
    was_independent = Column(Boolean, nullable=False, default=True)
    policy_version = Column(String(40), nullable=False, default="pedagogy-policy-v1")
    scheduler_shadow_version = Column(String(40), nullable=True)
    fsrs_predicted_recall = Column(Float, nullable=True)
    fsrs_next_review_at = Column(DateTime, nullable=True)
    fsrs_interval_days = Column(Float, nullable=True)
    fsrs_review_log_json = Column(JSON, nullable=True)
    
    # Relationships - Temporarily disabled to fix seed
    user = relationship("User", back_populates="review_events")
    card = relationship("Card", back_populates="review_events")
    # user_card_state = relationship("UserCardState", back_populates="review_events")
