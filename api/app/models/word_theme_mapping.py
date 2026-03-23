"""Word theme mapping model for FillTheWord analytics"""

from sqlalchemy import Column, Float, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.core.time import utc_now
import uuid


class WordThemeMapping(BaseModel):
    """Many-to-many relationship between words and themes with optional weights"""

    __tablename__ = "word_theme_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word_id = Column(UUID(as_uuid=True), ForeignKey('word.id'), nullable=False, comment="Word ID")
    theme_id = Column(UUID(as_uuid=True), ForeignKey('word_themes.id'), nullable=False, comment="Theme ID")
    weight = Column(Float, nullable=True, comment="Weight for multiple themes per word (0..1)")
    is_active = Column(Boolean, default=True, comment="Whether this mapping is active")
    created_at = Column(DateTime, default=utc_now, comment="Creation timestamp")
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, comment="Update timestamp")

    # Relationships
    word = relationship("Word", back_populates="theme_mappings")
    theme = relationship("WordTheme", back_populates="word_mappings")

    # Indexes for performance
    __table_args__ = (
        Index('idx_word_theme_mapping_word', 'word_id'),
        Index('idx_word_theme_mapping_theme', 'theme_id'),
        Index('idx_word_theme_mapping_active', 'is_active'),
        Index('idx_word_theme_mapping_word_theme', 'word_id', 'theme_id', unique=True),
    )

    def __repr__(self):
        return f"<WordThemeMapping(word_id='{self.word_id}', theme_id='{self.theme_id}', weight={self.weight})>"
