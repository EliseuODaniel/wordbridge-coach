"""User model for individual progress tracking"""

import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """User for SRS progress tracking"""

    __tablename__ = "user"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)  # Optional for MVP
    native_language_id = Column(UUID(as_uuid=True), ForeignKey("language.id"), nullable=False)
    target_language_id = Column(UUID(as_uuid=True), ForeignKey("language.id"), nullable=False)
    language_preference = Column(String(2), default="en", nullable=False)
    daily_new_limit = Column(Integer, default=10, nullable=False)
    easiness_factor = Column(Float, default=2.5, nullable=False)
    last_login = Column(DateTime, nullable=True)
    word_goal_rank = Column(Integer, default=1000, nullable=False)  # 100, 500, 1500, 3000, 5000, 10000
    mode = Column(String(20), default='spec4', nullable=False)  # 'spec4' | 'lingvist'
    accuracy_last_20 = Column(Float, nullable=True)  # Average of last 20 answers

    # Relationships
    native_language_obj = relationship("Language", foreign_keys=[native_language_id], back_populates="users_native")
    target_language_obj = relationship("Language", foreign_keys=[target_language_id], back_populates="users_target")
    card_states = relationship("UserCardState", back_populates="user")
    review_events = relationship("ReviewEvent", back_populates="user")
    word_stats = relationship("UserWordStats", back_populates="user")
    theme_stats = relationship("UserThemeStats", back_populates="user")
    daily_stats = relationship("UserDailyStats", back_populates="user")
    frequency_progress = relationship("UserFrequencyProgress", back_populates="user", uselist=False)
    session_stats = relationship("UserSessionStats", back_populates="user")
    
    # User settings as JSON for flexibility
    @property
    def settings(self):
        return {
            "new_cards_per_day": self.daily_new_limit,
            "auto_play_audio": True,
            "show_hints": True,
            "keyboard_shortcuts": True,
            "grammar_hints": True,
            "translation_enabled": True
        }
