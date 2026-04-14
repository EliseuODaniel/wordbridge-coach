"""
LLM Profile Registry for Chat Coach

Defines available LLM models with their capabilities and requirements.
Models are identified by profile_id and can be selected for chat or teacher analysis.
"""

from typing import Dict, Any, List
from pydantic import BaseModel


class LLMProfile(BaseModel):
    """LLM model profile definition"""
    id: str
    name: str
    provider: str  # 'llamacpp', 'openai_http', 'mock'
    model: str  # Model filename or API model name
    service_url: str  # llama.cpp service URL (e.g., "http://llm:8080")
    context_window: int
    supports_streaming: bool
    supports_json: bool
    estimated_vram: str  # e.g., "5.4GB"
    quality_tier: str  # 'low', 'medium', 'high'
    speed_tier: str  # 'slow', 'medium', 'fast'
    description: str = ""


# Available LLM profiles
# Each profile maps to a specific llama.cpp service (llm, llm_chat, llm_teacher)
LLM_PROFILES: Dict[str, LLMProfile] = {
    "gemma-4-e4b-it": LLMProfile(
        id="gemma-4-e4b-it",
        name="Gemma 4 E4B Instruct",
        provider="llamacpp",
        model="gemma-4-e4b-it",
        service_url="http://llm:8080",
        context_window=4096,
        supports_streaming=True,
        supports_json=True,
        estimated_vram="5.3GB",
        quality_tier="high",
        speed_tier="medium",
        description="Gemma 4 E4B quantized for llama.cpp; best default balance for the local 8GB VRAM setup"
    ),
    "phi-3-mini-4k-instruct": LLMProfile(
        id="phi-3-mini-4k-instruct",
        name="Phi-3 Mini 4K Instruct",
        provider="llamacpp",
        model="phi-3-mini-4k-instruct",
        service_url="http://llm_chat:8081",
        context_window=4096,
        supports_streaming=True,
        supports_json=True,
        estimated_vram="2.3GB",
        quality_tier="medium",
        speed_tier="fast",
        description="Microsoft's compact 3.8B parameter model, fast and efficient"
    ),
    "qwen2.5-3b-instruct": LLMProfile(
        id="qwen2.5-3b-instruct",
        name="Qwen2.5 3B Instruct",
        provider="llamacpp",
        model="qwen2.5-3b-instruct",
        service_url="http://llm_teacher:8082",
        context_window=2048,
        supports_streaming=True,
        supports_json=True,
        estimated_vram="2.1GB",
        quality_tier="medium",
        speed_tier="fast",
        description="Faster but less accurate, ideal for quick teacher analysis"
    ),
}

# Default profiles (used when user has no preference set)
DEFAULT_CHAT_PROFILE = "gemma-4-e4b-it"
DEFAULT_TEACHER_PROFILE = "gemma-4-e4b-it"


def get_profile(profile_id: str) -> LLMProfile:
    """
    Get LLM profile by ID.

    Args:
        profile_id: Profile identifier (e.g., "qwen2.5-7b-instruct")

    Returns:
        LLMProfile object

    Raises:
        ValueError: If profile_id not found
    """
    if profile_id not in LLM_PROFILES:
        raise ValueError(f"Invalid profile_id: {profile_id}. Available: {list(LLM_PROFILES.keys())}")
    return LLM_PROFILES[profile_id]


def list_profiles() -> List[LLMProfile]:
    """List all available LLM profiles."""
    return list(LLM_PROFILES.values())


def get_default_chat_profile() -> str:
    """Get default profile ID for chat."""
    return DEFAULT_CHAT_PROFILE


def get_default_teacher_profile() -> str:
    """Get default profile ID for teacher analysis."""
    return DEFAULT_TEACHER_PROFILE


def validate_profile_id(profile_id: str) -> bool:
    """Check if profile_id exists."""
    return profile_id in LLM_PROFILES
