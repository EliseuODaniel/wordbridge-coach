"""LLM Provider Factory

Reads feature flags and returns appropriate LLM provider.
Supports:
- MockLLMProvider (default)
- OpenAILLMProvider (optional, via HTTP)
"""

import os
import logging
from typing import Optional

from app.llm.provider_base import LLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.openai_provider import OpenAILLMProvider

logger = logging.getLogger(__name__)


def get_llm_provider_from_env() -> LLMProvider:
    """
    Read feature flags and return appropriate LLM provider.

    Feature Flags (environment variables):
    - CHAT_LLM_PROVIDER: 'mock' | 'openai_http' (default: 'mock')
    - CHAT_LLM_NETWORK_ENABLED: 'true' | 'false' (default: 'false')
    - CHAT_OPENAI_API_KEY: OpenAI API key (required for openai_http)
    - CHAT_OPENAI_MODEL: Model name (default: 'gpt-4o-mini')
    - CHAT_OPENAI_TIMEOUT_S: Timeout in seconds (default: 30)

    Returns:
        LLMProvider instance (Mock or OpenAI)

    Behavior:
    1. If CHAT_LLM_NETWORK_ENABLED=false → Always return Mock
    2. If CHAT_LLM_PROVIDER=mock → Return Mock
    3. If CHAT_LLM_PROVIDER=openai_http:
       - Check API key
       - If missing → Log warning, return Mock
       - If present → Return OpenAILLMProvider
    4. Default → Mock
    """
    # Check master network flag
    network_enabled = os.getenv("CHAT_LLM_NETWORK_ENABLED", "false").lower() == "true"

    if not network_enabled:
        logger.info("CHAT_LLM_NETWORK_ENABLED=false, using MockLLMProvider")
        return MockLLMProvider()

    # Check explicit provider selection
    provider = os.getenv("CHAT_LLM_PROVIDER", "mock").lower()

    if provider == "mock":
        logger.info("CHAT_LLM_PROVIDER=mock, using MockLLMProvider")
        return MockLLMProvider()

    elif provider == "openai_http":
        # Check for API key
        api_key = os.getenv("CHAT_OPENAI_API_KEY")

        if not api_key:
            logger.warning(
                "CHAT_LLM_PROVIDER=openai_http but CHAT_OPENAI_API_KEY not set, "
                "falling back to MockLLMProvider"
            )
            return MockLLMProvider()

        # Create OpenAI provider
        model = os.getenv("CHAT_OPENAI_MODEL", "gpt-4o-mini")
        timeout = int(os.getenv("CHAT_OPENAI_TIMEOUT_S", "30"))

        logger.info(
            f"Using OpenAILLMProvider (model={model}, timeout={timeout}s)"
        )

        return OpenAILLMProvider(
            api_key=api_key,
            model=model,
            timeout=timeout,
            fallback_to_mock=True
        )

    else:
        # Unknown provider, fallback to Mock
        logger.warning(
            f"Unknown CHAT_LLM_PROVIDER value: '{provider}', "
            f"falling back to MockLLMProvider"
        )
        return MockLLMProvider()


def get_provider_name(provider: LLMProvider) -> str:
    """Get human-readable name of provider instance."""
    if isinstance(provider, MockLLMProvider):
        return "MockLLMProvider"
    elif isinstance(provider, OpenAILLMProvider):
        return f"OpenAILLMProvider({provider.model})"
    else:
        return f"Unknown({type(provider).__name__})"
