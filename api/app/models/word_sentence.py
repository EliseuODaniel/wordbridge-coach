"""WordSentence model for many-to-many relationship between words and sentences"""

from sqlalchemy import Column, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class WordSentence(BaseModel):
    """Many-to-many relationship between words and sentences"""

    __tablename__ = "word_sentence"

    word_id = Column(UUID(as_uuid=True), ForeignKey("word.id"), nullable=False)
    sentence_id = Column(UUID(as_uuid=True), ForeignKey("sentence.id"), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)  # Mark primary example

    # Relationships
    word = relationship("Word", back_populates="sentence_mappings")
    sentence = relationship("Sentence", back_populates="word_mappings")

    # Indexes for performance
    __table_args__ = (
        {"schema": None},
    )