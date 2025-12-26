"""Pydantic schemas for Chat Coach operations (REST + WebSocket)"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


# ============================================================================
# REST Schemas (Conversation & Message Management)
# ============================================================================

class ChatConversationCreate(BaseModel):
    """Request schema for POST /api/v1/chat/conversations"""
    user_id: str = Field(..., description="User ID")
    title: str = Field(default="Practice Chat", description="Conversation title")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Practice Past Simple"
            }
        }


class ChatConversationResponse(BaseModel):
    """Response schema for chat conversation"""
    id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Conversation title")
    student_profile_json: Dict[str, Any] = Field(default_factory=dict, description="Student profile")
    lesson_frame_json: Dict[str, Any] = Field(default_factory=dict, description="Current lesson frame")
    session_summary: str = Field(default="", description="Session summary")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Practice Past Simple",
                "student_profile_json": {
                    "cefr_level": "A2",
                    "common_errors": ["past_simple", "articles"]
                },
                "lesson_frame_json": {
                    "cefr_target": "A2",
                    "learning_goal": "past_simple_practice",
                    "expected_intent": "describe_recent_activity",
                    "topic": "weekend_plans"
                },
                "session_summary": "",
                "created_at": "2025-12-25T10:00:00Z",
                "updated_at": "2025-12-25T10:00:00Z"
            }
        }


class ChatMessageResponse(BaseModel):
    """Response schema for chat message"""
    id: str = Field(..., description="Message ID")
    conversation_id: str = Field(..., description="Conversation ID")
    role: str = Field(..., description="Message role: system|user|assistant")
    content: str = Field(..., description="Message content")
    metadata_json: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440000",
                "conversation_id": "660e8400-e29b-41d4-a716-446655440000",
                "role": "assistant",
                "content": "Hello! Let's practice past simple. What did you do last weekend?",
                "metadata_json": {},
                "created_at": "2025-12-25T10:00:01Z"
            }
        }


# ============================================================================
# WebSocket Schemas (Real-time Communication)
# ============================================================================

# Client → Server Events

class DraftUpdate(BaseModel):
    """Client event: draft_update (sent while typing)"""
    type: str = Field(default="draft_update", description="Event type")
    conversation_id: str = Field(..., description="Conversation ID")
    draft_text: str = Field(..., description="Current draft text")
    cursor: int = Field(default=0, description="Cursor position")
    client_ts_ms: int = Field(..., description="Client timestamp (milliseconds)")


class UserMessageIn(BaseModel):
    """Client event: user_message (send final message)"""
    type: str = Field(default="user_message", description="Event type")
    conversation_id: str = Field(..., description="Conversation ID")
    content: str = Field(..., description="Message content")
    client_ts_ms: int = Field(..., description="Client timestamp (milliseconds)")


class RequestAutocomplete(BaseModel):
    """Client event: request_autocomplete (after idle time)"""
    type: str = Field(default="request_autocomplete", description="Event type")
    conversation_id: str = Field(..., description="Conversation ID")
    draft_text: str = Field(..., description="Current draft text")
    client_ts_ms: int = Field(..., description="Client timestamp (milliseconds)")
    mode: str = Field(default="soft", description="idle mode: soft|hard")


class Ping(BaseModel):
    """Client event: ping (heartbeat)"""
    type: str = Field(default="ping", description="Event type")
    ts: int = Field(..., description="Timestamp (milliseconds)")


# Server → Client Events

class DraftIssue(BaseModel):
    """Issue detected in draft (spelling, grammar, syntax, etc.)"""
    category: str = Field(..., description="Issue category: spelling|grammar|syntax|semantic|style")
    title: str = Field(..., description="Issue title")
    explanation: str = Field(..., description="Short explanation")
    highlight_spans: List[Dict[str, int]] = Field(default_factory=list, description="Character spans to highlight")
    suggestions: List[str] = Field(default_factory=list, description="Suggested corrections")

    class Config:
        json_schema_extra = {
            "example": {
                "category": "grammar",
                "title": "Verb tense",
                "explanation": "Use past simple for yesterday: 'go' → 'went'",
                "highlight_spans": [{"start": 2, "end": 4}],
                "suggestions": ["went", "traveled", "drove"]
            }
        }


class DraftFeedbackOut(BaseModel):
    """Server event: draft_feedback (response to draft_update)"""
    type: str = Field(default="draft_feedback", description="Event type")
    conversation_id: str = Field(..., description="Conversation ID")
    bar_score_raw: float = Field(..., description="Raw score 0-100")
    bar_score_components: Dict[str, float] = Field(..., description="Score components breakdown")
    lesson_alignment_score: float = Field(..., description="Lesson alignment score")
    issues: List[DraftIssue] = Field(default_factory=list, description="Detected issues")
    ghost_suggestion: Optional[str] = Field(None, description="Ghost text suggestion")
    micro_tip: Optional[str] = Field(None, description="Helpful tip shown when issues=[]")
    suggested_next_words: List[str] = Field(default_factory=list, description="Suggested next words to complete the phrase")
    topic: Optional[str] = Field(None, description="Detected conversation topic")
    intent: Optional[str] = Field(None, description="Detected user intent")
    rewrite: Optional[str] = Field(None, description="Suggested rewrite of the entire draft")
    draft: str = Field(default="", description="Draft text (for debugging/display)")
    server_ts_ms: int = Field(..., description="Server timestamp (milliseconds)")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "draft_feedback",
                "conversation_id": "660e8400-e29b-41d4-a716-446655440000",
                "bar_score_raw": 45.0,
                "bar_score_components": {
                    "spelling": 100.0,
                    "grammar": 20.0,
                    "syntax": 80.0,
                    "lesson_alignment": 30.0,
                    "naturalness": 50.0
                },
                "lesson_alignment_score": 30.0,
                "issues": [
                    {
                        "category": "grammar",
                        "title": "Verb tense",
                        "explanation": "Use past simple: 'go' → 'went'",
                        "highlight_spans": [{"start": 2, "end": 4}],
                        "suggestions": ["went", "traveled"]
                    }
                ],
                "ghost_suggestion": "went to the",
                "server_ts_ms": 1735132810050
            }
        }


class AssistantStreamTokenOut(BaseModel):
    """Server event: assistant_stream_token (streaming response)"""
    type: str = Field(default="assistant_stream_token", description="Event type")
    conversation_id: str = Field(..., description="Conversation ID")
    token: str = Field(..., description="Token from LLM")


class AssistantDoneOut(BaseModel):
    """Server event: assistant_done (end of streaming)"""
    type: str = Field(default="assistant_done", description="Event type")
    conversation_id: str = Field(..., description="Conversation ID")
    full_content: str = Field(..., description="Complete assistant response")
    lesson_frame: Dict[str, Any] = Field(..., description="Updated lesson frame")
    summary_update: Optional[str] = Field(None, description="Session summary delta")


class ErrorOut(BaseModel):
    """Server event: error"""
    type: str = Field(default="error", description="Event type")
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")


class Pong(BaseModel):
    """Server event: pong (response to ping)"""
    type: str = Field(default="pong", description="Event type")
    ts: int = Field(..., description="Timestamp (milliseconds)")


class Correction(BaseModel):
    """Single correction from teacher analysis"""
    mistake: str = Field(..., description="Original mistake")
    fix: str = Field(..., description="Corrected version")
    why: str = Field(..., description="Explanation of why this is correct")


class TeacherAnalysisOut(BaseModel):
    """Server event: teacher_analysis (separate from chat messages)"""
    type: str = Field(default="teacher_analysis", description="Event type")
    conversation_id: str = Field(..., description="Conversation ID")
    user_message_id: str = Field(..., description="ID of user message being analyzed")
    analysis: Dict[str, Any] = Field(..., description="Teacher analysis JSON with keys: rewrite, corrections, teacher_summary, next_practice")
