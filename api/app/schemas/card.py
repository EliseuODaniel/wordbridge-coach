"""Pydantic schemas for Card operations"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
import uuid

from app.core.time import utc_now


class Gap(BaseModel):
    """Gap information for fill-in-the-blank"""
    start: int = Field(..., description="Start position of gap")
    end: int = Field(..., description="End position of gap")


class LearningContext(BaseModel):
    """Compact pedagogical context shared across study modes."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "mode": "spec4",
            "cefr_level": "A2",
            "support_level": "guided_practice",
            "current_focus": "Use past simple after yesterday",
            "session_goal": "stabilize past-time verbs in short personal sentences",
            "topic": "travel",
            "feedback_language": "Portuguese",
            "why_this_now": "Recognition practice to reinforce the current focus before freer production.",
        }
    })

    mode: str = Field(..., description="Study mode that is consuming the context")
    cefr_level: str = Field(..., description="Current estimated learner level")
    support_level: str = Field(..., description="Current scaffolding level")
    current_focus: str = Field(..., description="Top current pedagogical focus")
    session_goal: str = Field(..., description="Current session objective")
    topic: str = Field(..., description="Recommended topic anchor")
    feedback_language: str = Field(..., description="Language used for explicit feedback")
    why_this_now: str = Field(..., description="Why this card mode is useful right now")
    retention_signal: Optional[str] = Field(
        None,
        description="How stable the learner retention looks right now (fragile|building|stable)",
    )
    review_pressure: Optional[str] = Field(
        None,
        description="Whether the learner is carrying low, medium, or high review pressure",
    )
    difficulty_signal: Optional[str] = Field(
        None,
        description="Whether the current mode should stabilize, stay on target, or stretch difficulty",
    )
    recommended_pace: Optional[str] = Field(
        None,
        description="Suggested pacing for the next turns (stabilize|balance|accelerate)",
    )
    next_mode_hint: Optional[str] = Field(
        None,
        description="Which mode would currently be the best next step if the learner switches",
    )


class CardResponse(BaseModel):
    """Response schema for GET /api/cards/next - EXACT match to specification"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "card_id": "550e8400-e29b-41d4-a716-446655440000",
            "word_id": "660e8400-e29b-41d4-a716-446655440000",
            "sentence_id": "770e8400-e29b-41d4-a716-446655440000",
            "word": "book",
            "sentence": "The ___ is on the table.",
            "gap": {"start": 4, "end": 8},
            "sentence_translation": "O livro está na mesa.",
            "grammar_hint": "É um objeto que você lê",
            "memory_stage": "LEARNING",
            "audio_word_url": "/api/tts/word/550e8400-e29b-41d4-a716-446655440000?text=book&lang=en",
            "audio_sentence_url": "/api/tts/sentence/550e8400-e29b-41d4-a716-446655440000?text=The%20book%20is%20on%20the%20table.&lang=en"
        }
    })

    card_id: str = Field(..., description="Unique card identifier")
    word_id: str = Field(..., description="Word ID for insights")
    sentence_id: str = Field(..., description="Sentence ID for variety tracking (Spec4)")
    word: str = Field(..., description="The word being studied")
    sentence: str = Field(..., description="Sentence with gap placeholder")
    gap: Gap = Field(..., description="Gap position information")
    sentence_translation: str = Field(..., description="Translation of complete sentence")
    grammar_hint: str = Field(..., description="Grammar hint for the word")
    memory_stage: str = Field(..., description="SM-2 memory stage")
    is_new: bool = Field(..., description="Whether this is a new word or review")
    audio_word_url: str = Field(..., description="URL for word audio")
    audio_sentence_url: str = Field(..., description="URL for sentence audio")
    sentence_source: Optional[str] = Field(None, description="Source title (e.g., 'Dracula') if from sentence bank")
    learning_context: Optional[LearningContext] = Field(
        None,
        description="Shared pedagogical context that explains why this card is useful now",
    )
    
class AnswerRequest(BaseModel):
    """Request schema for POST /api/cards/{id}/answer"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "answer": "book",
            "response_time_ms": 3200,
            "attempts": 1,
            "hints_used": 0
        }
    })

    answer: str = Field(..., description="User's answer")
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    attempts: int = Field(default=1, description="Number of attempts taken")
    hints_used: int = Field(default=0, description="Number of hints used")

class AnswerResponse(BaseModel):
    """Response schema for POST /api/cards/{id}/answer - EXACT match to specification"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "correct": True,
            "correct_answer": "book",
            "sentence_full": "The book is on the table.",
            "quality": 5,
            "next_review_at": "2024-01-21T10:00:00Z"
        }
    })

    correct: bool = Field(..., description="Whether answer was correct")
    correct_answer: str = Field(..., description="The correct answer")
    sentence_full: str = Field(..., description="Complete sentence with correct answer")
    quality: int = Field(..., description="SM-2 quality score (0-5)")
    next_review_at: datetime = Field(..., description="When to review this card next")
    
class ErrorResponse(BaseModel):
    """Standard error response"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "error": "card_not_found",
            "message": "Card not found",
            "timestamp": "2024-01-15T10:00:00Z"
        }
    })

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human readable message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=utc_now, description="Error timestamp")
