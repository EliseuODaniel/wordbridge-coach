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
    context_window: int
    supports_streaming: bool
    supports_json: bool
    estimated_vram: str  # e.g., "5.4GB"
    quality_tier: str  # 'low', 'medium', 'high'
    speed_tier: str  # 'slow', 'medium', 'fast'
    description: str = ""


# Available LLM profiles
# TODO: Add more models as needed (phi-3-mini, gemma-2-9b, mistral-7b, etc.)
LLM_PROFILES: Dict[str, LLMProfile] = {
    "qwen2.5-7b-instruct": LLMProfile(
        id="qwen2.5-7b-instruct",
        name="Qwen2.5 7B Instruct",
        provider="llamacpp",
        model="qwen2.5-7b-instruct",
        context_window=4096,
        supports_streaming=True,
        supports_json=True,
        estimated_vram="5.4GB",
        quality_tier="high",
        speed_tier="medium",
        description="High-quality Chinese/English bilingual model, good for teaching"
    ),
    "qwen2.5-3b-instruct": LLMProfile(
        id="qwen2.5-3b-instruct",
        name="Qwen2.5 3B Instruct",
        provider="llamacpp",
        model="qwen2.5-3b-instruct",
        context_window=4096,
        supports_streaming=True,
        supports_json=True,
        estimated_vram="2.1GB",
        quality_tier="medium",
        speed_tier="fast",
        description="Faster but less accurate, good for quick chat responses"
    ),
    "llama-3.1-8b-instruct": LLMProfile(
        id="llama-3.1-8b-instruct",
        name="Llama 3.1 8B Instruct",
        provider="llamacpp",
        model="llama-3.1-8b-instruct",
        context_window=4096,
        supports_streaming=True,
        supports_json=True,
        estimated_vram="5.7GB",
        quality_tier="high",
        speed_tier="medium",
        description="Meta's flagship instruction-tuned model, excellent for English"
    ),
}

# Default profiles (used when user has no preference set)
DEFAULT_CHAT_PROFILE = "qwen2.5-7b-instruct"
DEFAULT_TEACHER_PROFILE = "qwen2.5-7b-instruct"


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
