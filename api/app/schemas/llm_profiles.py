"""Pydantic schemas for LLM Profile management"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
import uuid


# ============================================================================
# LLM Profile Schemas
# ============================================================================

class LLMProfileResponse(BaseModel):
    """Response schema for a single LLM profile"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "gemma-4-e4b-it",
            "name": "Gemma 4 E4B Instruct",
            "provider": "llamacpp",
            "model": "gemma-4-e4b-it",
            "service_url": "http://llm:8080",
            "context_window": 4096,
            "supports_streaming": True,
            "supports_json": True,
            "estimated_vram": "5.3GB",
            "quality_tier": "high",
            "speed_tier": "medium",
            "description": "Gemma 4 E4B quantized for llama.cpp"
        }
    })

    id: str = Field(..., description="Profile ID (e.g., 'gemma-4-e4b-it')")
    name: str = Field(..., description="Human-readable name")
    provider: str = Field(..., description="Provider type (llamacpp, openai_http, mock)")
    model: str = Field(..., description="Model identifier")
    service_url: str = Field(..., description="llama.cpp service URL (e.g., 'http://llm:8080')")
    context_window: int = Field(..., description="Max context tokens")
    supports_streaming: bool = Field(..., description="Supports streaming responses")
    supports_json: bool = Field(..., description="Supports JSON mode")
    estimated_vram: str = Field(..., description="Estimated VRAM usage (e.g., '5.4GB')")
    quality_tier: str = Field(..., description="Quality tier (low, medium, high)")
    speed_tier: str = Field(..., description="Speed tier (slow, medium, fast)")
    description: str = Field(default="", description="Human-readable description")

class LLMProfileListResponse(BaseModel):
    """Response schema for GET /api/v1/llm-profiles"""
    profiles: List[LLMProfileResponse] = Field(..., description="Available LLM profiles")


# ============================================================================
# User LLM Preferences Schemas
# ============================================================================

class UserLLMPreferencesResponse(BaseModel):
    """Response schema for user's LLM preferences"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "660e8400-e29b-41d4-a716-446655440000",
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "chat_model_profile": "gemma-4-e4b-it",
            "teacher_model_profile": "gemma-4-e4b-it",
            "created_at": "2025-12-26T15:00:00Z",
            "updated_at": "2025-12-26T15:00:00Z"
        }
    })

    id: str = Field(..., description="Preferences ID")
    user_id: str = Field(..., description="User ID")
    chat_model_profile: str = Field(..., description="Selected chat model profile ID")
    teacher_model_profile: str = Field(..., description="Selected teacher model profile ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

class UserLLMPreferencesUpdate(BaseModel):
    """Request schema for PUT /api/v1/users/me/llm-preferences"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "chat_model_profile": "gemma-4-e4b-it",
            "teacher_model_profile": "qwen2.5-3b-instruct"
        }
    })

    chat_model_profile: Optional[str] = Field(
        None,
        description="Chat model profile ID (null = no change)"
    )
    teacher_model_profile: Optional[str] = Field(
        None,
        description="Teacher model profile ID (null = no change)"
    )
