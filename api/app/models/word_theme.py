"""Word theme model for FillTheWord analytics"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import uuid
from datetime import datetime


class WordTheme(BaseModel):
    """Thematic categories for words (Daily actions, Travel, Emotions, etc.)"""

    __tablename__ = "word_themes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, comment="Theme name (ex: Daily actions, Travel)")
    description = Column(Text, nullable=True, comment="Optional description of the theme")
    is_active = Column(Boolean, default=True, comment="Whether this theme is active")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Creation timestamp")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Update timestamp")

    # Relationships
    word_mappings = relationship("WordThemeMapping", back_populates="theme")
    user_stats = relationship("UserThemeStats", back_populates="theme")

    # Indexes for performance
    __table_args__ = (
        Index('idx_word_theme_name', 'name'),
        Index('idx_word_theme_active', 'is_active'),
    )

    def __repr__(self):
        return f"<WordTheme(name='{self.name}', id='{self.id}')>"