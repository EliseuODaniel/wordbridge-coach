"""Word model for vocabulary"""

from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Word(BaseModel):
    """Individual vocabulary word"""

    __tablename__ = "word"

    lemma = Column(String(100), nullable=False, index=True)  # Base dictionary form
    text = Column(String(100), nullable=False)  # Specific form used
    part_of_speech = Column(String(20), nullable=False)  # noun, verb, adjective, etc.
    features = Column(JSON, nullable=True)  # Grammatical properties
    language_id = Column(UUID(as_uuid=True), ForeignKey("language.id"), nullable=False)
    pronunciation = Column(String(200), nullable=True)  # IPA notation
    frequency_rank = Column(Integer, nullable=True)  # Common word frequency (1=most common)
    audio_path = Column(String(500), nullable=True)  # Path to cached TTS audio
    difficulty = Column(Integer, nullable=False, default=1)  # 1-5
    
    # Relationships
    language = relationship("Language", back_populates="words")
    sentences = relationship("Sentence", back_populates="word")
    sentence_mappings = relationship("WordSentence", back_populates="word")
    user_stats = relationship("UserWordStats", back_populates="word")
    theme_mappings = relationship("WordThemeMapping", back_populates="word")
    
  