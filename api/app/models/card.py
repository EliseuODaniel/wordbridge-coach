"""Card model for study content"""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Card(BaseModel):
    """Study card with fill-in-the-gap content"""

    __tablename__ = "card"

    sentence_id = Column(UUID(as_uuid=True), ForeignKey("sentence.id"), nullable=False)
    deck_id = Column(UUID(as_uuid=True), ForeignKey("deck.id"), nullable=False)
    grammar_hint = Column(String(500), nullable=False)
    difficulty = Column(Integer, nullable=False, default=1)  # 1-5
    position = Column(Integer, nullable=True)  # Legacy gap position
    gap_start = Column(Integer, nullable=False)  # Gap start index
    gap_end = Column(Integer, nullable=False)  # Gap end index
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    sentence = relationship("Sentence", back_populates="card")
    deck = relationship("Deck", back_populates="cards")
    user_states = relationship("UserCardState", back_populates="card")
    review_events = relationship("ReviewEvent", back_populates="card")
    
    @property
    def sentence_with_gap(self):
        """Return sentence with visual gap"""
        if self.sentence:
            text = self.sentence.text
            return text[:self.gap_start] + "___" + text[self.gap_end:]
        return ""
    
    @property
    def target_word(self):
        """Get the target word that fills the gap"""
        if self.sentence and self.sentence.word:
            return self.sentence.word.text
        return ""
    
    @property
    def context_before(self):
        """Text before the gap"""
        if self.sentence:
            return self.sentence.text[:self.gap_start]
        return ""
    
    @property
    def context_after(self):
        """Text after the gap"""
        if self.sentence:
            return self.sentence.text[self.gap_end:]
        return ""
