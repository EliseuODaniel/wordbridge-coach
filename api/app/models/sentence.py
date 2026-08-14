"""Sentence model for fill-in-the-gap cards"""

from sqlalchemy import Boolean, Column, String, Integer, ForeignKey, Enum, JSON
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

    # Source metadata (v1.1 enhancement)
    source_title = Column(String(200), nullable=True)  # Book title, e.g., "Dracula"
    source_author = Column(String(200), nullable=True)  # Author, e.g., "Bram Stoker"
    source_ref = Column(String(50), nullable=True)  # Reference, e.g., "gutenberg:345"

    # Pedagogical content contract. Existing literary rows remain usable but
    # are no longer mistaken for contemporary, reviewed course material.
    cefr_level = Column(String(16), nullable=True)
    register = Column(String(32), nullable=False, default="neutral")
    domain = Column(String(64), nullable=True)
    competency_codes = Column(JSON, nullable=False, default=list)
    grammar_tags = Column(JSON, nullable=False, default=list)
    quality_status = Column(String(24), nullable=False, default="unreviewed")
    license_name = Column(String(120), nullable=True)
    content_version = Column(String(40), nullable=False, default="legacy-v1")
    is_contemporary = Column(Boolean, nullable=False, default=False)

    # Relationships
    word = relationship("Word", back_populates="sentences")
    language = relationship("Language", back_populates="sentences")
    word_mappings = relationship("WordSentence", back_populates="sentence")
    card = relationship("Card", back_populates="sentence", uselist=False)
