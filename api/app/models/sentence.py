"""Sentence model for fill-in-the-gap cards"""

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Sentence(BaseModel):
    """Sentences used in cards with translation"""

    text = Column(String(1000), nullable=False)
    translation = Column(String(1000), nullable=False)
    word_id = Column(UUID(as_uuid=True), ForeignKey("word.id"), nullable=False)
    language_id = Column(UUID(as_uuid=True), ForeignKey("language.id"), nullable=False)
    type = Column(String(20), nullable=False, default="example")  # example, usage, definition
    difficulty = Column(Integer, nullable=False, default=1)  # 1-5
    audio_path = Column(String(500), nullable=True)  # Path to cached TTS audio
    gap_start = Column(Integer, nullable=False)  # Gap start position
    gap_end = Column(Integer, nullable=False)  # Gap end position

    # Relationships
    word = relationship("Word", back_populates="sentences")
    language = relationship("Language", back_populates="sentences")
    card = relationship("Card", back_populates="sentence", uselist=False)
