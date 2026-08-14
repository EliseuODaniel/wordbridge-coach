"""User LLM Preferences model for Chat Coach model selection"""

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class UserLLMPreferences(BaseModel):
    """
    User preferences for LLM model selection in Chat Coach.

    Allows users to choose different models for chat vs teacher analysis.
    Persists per-user preferences (survives browser clear).
    """

    __tablename__ = "user_llm_preferences"

    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
        index=True,
        unique=True,
    )

    # LLM profile IDs (referencing app/llm/profiles.py:LLM_PROFILES)
    # Chat model: used for conversational responses (streaming)
    chat_model_profile = Column(
        String(100),
        nullable=False,
        default="qwen2.5-7b-instruct"
    )

    # Teacher model: used for teacher analysis JSON (non-streaming)
    teacher_model_profile = Column(
        String(100),
        nullable=False,
        default="qwen2.5-7b-instruct"
    )

    # Note: id, created_at, updated_at are inherited from BaseModel

    def __repr__(self):
        return f"<UserLLMPreferences(user_id={self.user_id}, chat={self.chat_model_profile}, teacher={self.teacher_model_profile})>"
