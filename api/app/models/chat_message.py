"""ChatMessage model for Chat Coach mode"""

import enum
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class MessageRole(enum.Enum):
    """Role of the message sender"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Individual message within a Chat Coach conversation"""

    __tablename__ = "chat_messages"

    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(String(20), nullable=False)  # 'system', 'user', 'assistant'
    content = Column(Text, nullable=False)
    metadata_json = Column(JSONB, default={}, nullable=True)
    """
    Optional metadata for the message
    Example:
    {
        "lesson_frame_snapshot": { ... },
        "scores": { "grammar": 80, "spelling": 100 },
        "tokens": 150
    }
    """

    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")
