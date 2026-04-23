"""Word frequency model for WordBridge Coach."""

from sqlalchemy import Column, String, Integer, Float, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
import uuid


class WordFrequency(BaseModel):
    """Word frequency ranking for intelligent card selection"""

    __tablename__ = "word_frequencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word = Column(String(100), nullable=False, comment="Lowercase word")
    language_code = Column(String(10), nullable=False, default="en", comment="Language code (en, fr, etc.)")
    rank = Column(Integer, nullable=False, comment="Frequency rank (1=most frequent)")
    frequency_score = Column(Float, nullable=True, comment="Normalized frequency score")
    coverage_pct = Column(Float, nullable=True, comment="Cumulative coverage percentage (0-100)")
    band = Column(Integer, nullable=False, comment="Frequency band: 1(1-1000), 2(1001-3000), 3(3001-6000), 4(6001-10000)")
    is_active = Column(Boolean, default=True, comment="Whether this word is available for selection")

    # Indexes for performance
    __table_args__ = (
        Index('idx_word_frequency_word', 'word'),
        Index('idx_word_frequency_rank', 'rank'),
        Index('idx_word_frequency_band', 'band'),
        Index('idx_word_frequency_active_band', 'is_active', 'band'),
        Index('idx_word_frequency_lang_word', 'language_code', 'word'),
        Index('idx_word_frequency_lang_rank', 'language_code', 'rank'),
    )

    def __repr__(self):
        return f"<WordFrequency(word='{self.word}', rank={self.rank}, band={self.band})>"

    @classmethod
    def get_band_from_rank(cls, rank: int) -> int:
        """Convert rank to frequency band"""
        if rank <= 1000:
            return 1
        elif rank <= 3000:
            return 2
        elif rank <= 6000:
            return 3
        elif rank <= 10000:
            return 4
        else:
            return 5  # Beyond top 10k
