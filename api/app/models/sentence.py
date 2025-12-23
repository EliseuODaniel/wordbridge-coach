"""Sentence model for fill-in-the-gap cards"""

from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class SourceType(str, enum.Enum):
    CORPUS = "corpus"
    GENERATED = "generated"
    MANUAL = "manual"


class Sentence(BaseModel):
    """Sentences used in cards with translation"""

    __tablename__ = "sentence"

    text = Column(String(1000), nullable=False)
    translation = Column(String(1000), nullable=True)  # Can be null for some sources
    word_id = Column(UUID(as_uuid=True), ForeignKey("word.id"), nullable=False)
    language_id = Column(UUID(as_uuid=True), ForeignKey("language.id"), nullable=False)
    type = Column(String(50), nullable=False)  # Legacy column - required by DB
    source_type = Column(Enum(SourceType), default=SourceType.CORPUS, nullable=False)
    difficulty = Column(Integer, nullable=False, default=1)  # 1-5
    audio_path = Column(String(500), nullable=True)  # Path to cached TTS audio
    gap_start = Column(Integer, nullable=False)  # Gap start position
    gap_end = Column(Integer, nullable=False)  # Gap end position
    grammar_hint = Column(String(100), nullable=True)  # "verb, base form", "noun, plural", etc.

    # Relationships
    word = relationship("Word", back_populates="sentences")
    language = relationship("Language", back_populates="sentences")
    word_mappings = relationship("WordSentence", back_populates="sentence")
    card = relationship("Card", back_populates="sentence", uselist=False)
