"""ChatLessonHistory model for tracking Lesson Frame evolution (optional, Phase 2)"""

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ChatLessonHistory(BaseModel):
    """History of Lesson Frames for a conversation (optional, Phase 2)"""

    __tablename__ = "chat_lesson_history"

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    lesson_frame_json = Column(JSONB, nullable=False)
    """
    Snapshot of Lesson Frame at a point in time
    Useful for analytics: "How did pedagogical objectives evolve during conversation?"
    """

    # Relationships
    conversation = relationship("ChatConversation", back_populates="lesson_history")
