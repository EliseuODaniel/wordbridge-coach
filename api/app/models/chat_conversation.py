"""ChatConversation model for Chat Coach mode"""

import uuid
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ChatConversation(BaseModel):
    """Conversation between student and AI teacher for Chat Coach mode"""

    __tablename__ = "chat_conversations"

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    title = Column(String(255), default="New Chat", nullable=False)
    student_profile_json = Column(JSONB, default={}, nullable=False)
    """
    Student profile with CEFR level and common errors
    Example:
    {
        "cefr_level": "A2",
        "common_errors": ["past_simple", "articles", "prepositions"],
        "strengths": ["vocabulary", "basic_fluency"],
        "weaknesses": ["grammar", "irregular_verbs"]
    }
    """
    lesson_frame_json = Column(JSONB, default={}, nullable=False)
    """
    Pedagogical objective for current turn
    The persisted shape is defined by the active Chat Coach runtime.
    """
    session_summary = Column(Text, default="", nullable=False)

    # Relationships
    user = relationship("User", back_populates="chat_conversations")
    messages = relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at.asc()"
    )
    lesson_history = relationship(
        "ChatLessonHistory",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatLessonHistory.created_at.asc()"
    )
