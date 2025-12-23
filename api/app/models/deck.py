"""Deck model for organizing cards"""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Deck(BaseModel):
    """Categories of content organized by difficulty and topic"""

    name = Column(String(100), nullable=False)
    language_id = Column(UUID(as_uuid=True), ForeignKey("language.id"), nullable=False)
    difficulty_level = Column(Integer, nullable=False)  # 1-5
    description = Column(String(500), nullable=True)
    card_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    language = relationship("Language", back_populates="decks")
    cards = relationship("Card", back_populates="deck")
