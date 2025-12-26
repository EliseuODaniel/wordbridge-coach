"""LLM Provider Factory

Reads feature flags and returns appropriate LLM provider.
Supports:
- LlamaCppLLMProvider (default, local)
- OpenAILLMProvider (optional, cloud)
- MockLLMProvider (fallback)
"""

import os
import logging
from typing import Optional

from app.llm.provider_base import LLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_provider import OpenAILLMProvider
from app.llm.llamacpp_provider import LlamaCppLLMProvider

logger = logging.getLogger(__name__)


def get_llm_provider_from_env() -> LLMProvider:
    """
    Read feature flags and return appropriate LLM provider.

    Feature Flags (environment variables):
    - CHAT_LLM_PROVIDER: 'mock' | 'openai_http' | 'llamacpp' (default: 'llamacpp')
    - CHAT_LLM_STRICT: 'true' | 'false' (default: 'false')
    - CHAT_LLM_NETWORK_ENABLED: 'true' | 'false' (default: 'false')
    - CHAT_LLM_BASE_URL: Base URL with /v1 suffix (required for llamacpp/openai_http)
    - CHAT_LLM_MODEL: Model name (default varies by provider)
    - CHAT_OPENAI_API_KEY: OpenAI API key (required for openai_http)
    - CHAT_OPENAI_TIMEOUT_S: Timeout in seconds (default varies by provider)

    Returns:
        LLMProvider instance (LlamaCpp, OpenAI, or Mock)

    Behavior:
    1. If CHAT_LLM_PROVIDER=llamacpp (default):
       - Local LLM, ignores CHAT_LLM_NETWORK_ENABLED
       - Requires CHAT_LLM_BASE_URL
       - If strict=True and error → Raise exception
       - If strict=False and error → Fallback to Mock

    2. If CHAT_LLM_PROVIDER=openai_http:
       - Cloud LLM, respects CHAT_LLM_NETWORK_ENABLED
       - Requires CHAT_OPENAI_API_KEY
       - If strict=True and error → Raise exception
       - If strict=False and error → Fallback to Mock

    3. If CHAT_LLM_PROVIDER=mock:
       - Always return MockLLMProvider

    4. Unknown provider → Fallback to Mock with warning
    """
    provider = os.getenv("CHAT_LLM_PROVIDER", "llamacpp").lower()
    strict = os.getenv("CHAT_LLM_STRICT", "false").lower() == "true"

    # =========================================================================
    # Local LLM (llamacpp) - ignores CHAT_LLM_NETWORK_ENABLED
    # =========================================================================
    if provider == "llamacpp":
        base_url = os.getenv("CHAT_LLM_BASE_URL")
        if not base_url:
            msg = "CHAT_LLM_PROVIDER=llamacpp but CHAT_LLM_BASE_URL not set"
            if strict:
                raise ValueError(msg)
            logger.warning(f"{msg}, falling back to MockLLMProvider")
            return MockLLMProvider()

        model = os.getenv("CHAT_LLM_MODEL", "qwen2.5-7b-instruct")
        timeout = int(os.getenv("CHAT_OPENAI_TIMEOUT_S", "60"))

        logger.info(
            f"Using LlamaCppLLMProvider (model={model}, base_url={base_url}, strict={strict})"
        )

        return LlamaCppLLMProvider(
            base_url=base_url,
            model=model,
            timeout=timeout,
            strict=strict
        )

    # =========================================================================
    # OpenAI (external) - respects CHAT_LLM_NETWORK_ENABLED
    # =========================================================================
    elif provider == "openai_http":
        # Check network flag
        network_enabled = os.getenv("CHAT_LLM_NETWORK_ENABLED", "false").lower() == "true"
        if not network_enabled:
            msg = "CHAT_LLM_NETWORK_ENABLED=false"
            if strict:
                raise ValueError(f"{msg} but CHAT_LLM_STRICT=true")
            logger.info(f"{msg}, using MockLLMProvider")
            return MockLLMProvider()

        # Check API key
        api_key = os.getenv("CHAT_OPENAI_API_KEY")
        if not api_key:
            msg = "CHAT_LLM_PROVIDER=openai_http but CHAT_OPENAI_API_KEY not set"
            if strict:
                raise ValueError(msg)
            logger.warning(f"{msg}, falling back to MockLLMProvider")
            return MockLLMProvider()

        # Create OpenAI provider
        model = os.getenv("CHAT_OPENAI_MODEL", "gpt-4o-mini")
        timeout = int(os.getenv("CHAT_OPENAI_TIMEOUT_S", "30"))

        logger.info(
            f"Using OpenAILLMProvider (model={model}, strict={strict})"
        )

        # Map strict to fallback_to_mock (opposite)
        fallback_to_mock = not strict

        return OpenAILLMProvider(
            api_key=api_key,
            model=model,
            timeout=timeout,
            fallback_to_mock=fallback_to_mock
        )

    # =========================================================================
    # Mock (explicit)
    # =========================================================================
    elif provider == "mock":
        logger.info("CHAT_LLM_PROVIDER=mock, using MockLLMProvider")
        return MockLLMProvider()

    # =========================================================================
    # Unknown provider → Fallback to Mock
    # =========================================================================
    else:
        logger.warning(
            f"Unknown CHAT_LLM_PROVIDER value: '{provider}', "
            f"falling back to MockLLMProvider"
        )
        return MockLLMProvider()


def get_provider_name(provider: LLMProvider) -> str:
    """Get human-readable name and config of provider instance."""
    if isinstance(provider, MockLLMProvider):
        return "MockLLMProvider"
    elif isinstance(provider, LlamaCppLLMProvider):
        return f"LlamaCppLLMProvider(model={provider.model}, base_url={provider.base_url}, strict={provider.strict})"
    elif isinstance(provider, OpenAILLMProvider):
        return f"OpenAILLMProvider(model={provider.model}, strict={not provider.fallback_to_mock})"
    else:
        return f"Unknown({type(provider).__name__})"


def get_llm_provider_for_profile(profile_id: str) -> LLMProvider:
    """
    Get LLM provider for a specific profile ID.

    Reads profile configuration from profiles.py and creates appropriate provider.
    Each profile has its own service_url, enabling multi-model routing.

    Args:
        profile_id: Profile ID (e.g., "qwen2.5-7b-instruct", "phi-3-mini-4k-instruct")

    Returns:
        LLMProvider instance configured for the specified profile

    Raises:
        ValueError: If profile_id not found or provider unsupported
    """
    from app.llm.profiles import get_profile

    # Get profile configuration
    profile = get_profile(profile_id)

    # Currently all profiles use llamacpp provider
    # Future: support openai_http, mock providers via profile.provider field
    if profile.provider != "llamacpp":
        raise ValueError(f"Unsupported provider in profile: {profile.provider}")

    # Use service_url from profile (each profile maps to specific llama.cpp service)
    base_url = profile.service_url

    timeout = int(os.getenv("CHAT_OPENAI_TIMEOUT_S", "60"))
    strict = os.getenv("CHAT_LLM_STRICT", "false").lower() == "true"

    # Create provider with profile-specific model name and service URL
    logger.info(
        f"Creating LlamaCppLLMProvider for profile '{profile_id}' "
        f"(model={profile.model}, base_url={base_url})"
    )

    return LlamaCppLLMProvider(
        base_url=base_url,  # Use service_url from profile
        model=profile.model,  # Use model name from profile
        timeout=timeout,
        strict=strict
    )

