"""Language model for TTS configuration"""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Language(BaseModel):
    """Supported languages with TTS configuration"""
    
    code = Column(String(2), unique=True, nullable=False, index=True)  # ISO 639-1
    name = Column(String(50), nullable=False)
    voice_model = Column(String(100), nullable=False)
    voice_type = Column(String(20), nullable=False)  # male, female, neutral
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    words = relationship("Word", back_populates="language")
    sentences = relationship("Sentence", back_populates="language")
    decks = relationship("Deck", back_populates="language")
    users_native = relationship("User", foreign_keys="User.native_language_id", back_populates="native_language_obj")
    users_target = relationship("User", foreign_keys="User.target_language_id", back_populates="target_language_obj")
