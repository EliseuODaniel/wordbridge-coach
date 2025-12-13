"""Pydantic schemas for Card operations"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class Gap(BaseModel):
    """Gap information for fill-in-the-blank"""
    start: int = Field(..., description="Start position of gap")
    end: int = Field(..., description="End position of gap")


class CardResponse(BaseModel):
    """Response schema for GET /api/cards/next - EXACT match to specification"""
    card_id: str = Field(..., description="Unique card identifier")
    sentence: str = Field(..., description="Sentence with gap placeholder")
    gap: Gap = Field(..., description="Gap position information")
    sentence_translation: str = Field(..., description="Translation of complete sentence")
    grammar_hint: str = Field(..., description="Grammar hint for the word")
    memory_stage: str = Field(..., description="SM-2 memory stage")
    audio_word_url: str = Field(..., description="URL for word audio")
    audio_sentence_url: str = Field(..., description="URL for sentence audio")
    
    class Config:
        json_schema_extra = {
            "example": {
                "card_id": "550e8400-e29b-41d4-a716-446655440000",
                "sentence": "The ___ is on the table.",
                "gap": {"start": 4, "end": 8},
                "sentence_translation": "O livro está na mesa.",
                "grammar_hint": "É um objeto que você lê",
                "memory_stage": "learning",
                "audio_word_url": "/api/audio/en/word/abc123.wav",
                "audio_sentence_url": "/api/audio/en/sentence/def456.wav"
            }
        }


class AnswerRequest(BaseModel):
    """Request schema for POST /api/cards/{id}/answer"""
    answer: str = Field(..., description="User's answer")
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "book",
                "response_time_ms": 3200
            }
        }


class AnswerResponse(BaseModel):
    """Response schema for POST /api/cards/{id}/answer - EXACT match to specification"""
    correct: bool = Field(..., description="Whether answer was correct")
    correct_answer: str = Field(..., description="The correct answer")
    sentence_full: str = Field(..., description="Complete sentence with correct answer")
    quality: int = Field(..., description="SM-2 quality score (0-5)")
    next_review_at: datetime = Field(..., description="When to review this card next")
    
    class Config:
        json_schema_extra = {
            "example": {
                "correct": True,
                "correct_answer": "book",
                "sentence_full": "The book is on the table.",
                "quality": 5,
                "next_review_at": "2024-01-21T10:00:00Z"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human readable message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "card_not_found",
                "message": "Card not found",
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }
