"""Pydantic schemas for Lingvist mode"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

from app.schemas.card import Gap, LearningContext


class MicroProgress(BaseModel):
    """Micro progress for Lingvist mode session"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "current": 3,
            "total": 10,
            "new_words": 2
        }
    })

    current: int = Field(..., description="Current card number in session")
    total: int = Field(..., description="Total cards in session")
    new_words: int = Field(..., description="Number of new words in session")


class LingvistCardResponse(BaseModel):
    """Response schema for GET /api/v1/cards/next-lingvist

    Enriched payload for Lingvist mode with inline input, progressive hints,
    and PT-BR translations.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "card_id": "550e8400-e29b-41d4-a716-446655440000",
            "word_id": "660e8400-e29b-41d4-a716-446655440000",
            "sentence_id": "770e8400-e29b-41d4-a716-446655440000",
            "word": "book",
            "sentence": "The ___ is on the table.",
            "gap": {"start": 4, "end": 7},
            "correct_answer": "book",
            "grammar_tag_pt": "substantivo, masculino, singular",
            "word_translation_pt": "livro",
            "sentence_translation_pt": "O livro está na mesa.",
            "sentence_source": "Dracula",
            "is_new": True,
            "micro_progress": {"current": 3, "total": 10, "new_words": 2},
            "audio_word_url": "/api/tts/word/550e8400-e29b-41d4-a716-446655440000?text=book&lang=en",
            "audio_sentence_url": "/api/tts/sentence/550e8400-e29b-41d4-a716-446655440000?text=The%20book%20is%20on%20the%20table.&lang=en"
        }
    })

    card_id: str = Field(..., description="Unique card identifier")
    word_id: str = Field(..., description="Word ID for insights")
    sentence_id: str = Field(..., description="Sentence ID for variety tracking")
    word: str = Field(..., description="The word being studied")
    sentence: str = Field(..., description="Sentence with gap placeholder")
    gap: Gap = Field(..., description="Gap position information")
    correct_answer: str = Field(..., description="Expected answer for validation")
    grammar_tag_pt: str = Field(..., description="Grammar tag in PT-BR (ex: 'substantivo, plural')")
    word_translation_pt: Optional[str] = Field(None, description="PT-BR translation of word")
    sentence_translation_pt: Optional[str] = Field(None, description="PT-BR translation of sentence")
    sentence_source: Optional[str] = Field(None, description="Source title if from sentence bank")
    is_new: bool = Field(..., description="Whether this is a new word or review")
    micro_progress: MicroProgress = Field(..., description="Session progress")
    audio_word_url: str = Field(..., description="URL for word audio")
    audio_sentence_url: str = Field(..., description="URL for sentence audio (play after correct)")
    learning_context: Optional[LearningContext] = Field(
        None,
        description="Shared pedagogical context that explains the current Lingvist focus",
    )
