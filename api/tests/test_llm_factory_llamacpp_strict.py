"""
Test LLM Provider Factory with llamacpp strict mode

Tests:
- Factory returns LlamaCppLLMProvider with correct config
- Strict mode prevents fallback
- Environment variable parsing
"""

import pytest
import os
from unittest.mock import patch

from app.llm.factory import get_llm_provider_from_env
from app.llm.llamacpp_provider import LlamaCppLLMProvider
from app.llm.mock_provider import MockLLMProvider


def test_factory_llamacpp_provider():
    """Test factory returns LlamaCppLLMProvider with correct config."""

    # Set environment variables
    env_vars = {
        "CHAT_LLM_PROVIDER": "llamacpp",
        "CHAT_LLM_BASE_URL": "http://llm:8080/v1",
        "CHAT_LLM_MODEL": "gemma-4-e4b-it",
        "CHAT_LLM_STRICT": "true"
    }

    with patch.dict(os.environ, env_vars, clear=True):
        provider = get_llm_provider_from_env()

        # Verify type
        assert isinstance(provider, LlamaCppLLMProvider)

        # Verify config
        assert provider.base_url == "http://llm:8080/v1"
        assert provider.model == "gemma-4-e4b-it"
        assert provider.strict is True


def test_factory_llamacpp_missing_base_url():
    """Test factory raises error when base_url missing with strict=True."""

    env_vars = {
        "CHAT_LLM_PROVIDER": "llamacpp",
        "CHAT_LLM_STRICT": "true"
        # CHAT_LLM_BASE_URL not set
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(ValueError, match="CHAT_LLM_BASE_URL not set"):
            get_llm_provider_from_env()


def test_factory_llamacpp_missing_base_url_non_strict():
    """Test factory falls back to Mock when base_url missing with strict=False."""

    env_vars = {
        "CHAT_LLM_PROVIDER": "llamacpp",
        "CHAT_LLM_STRICT": "false"
        # CHAT_LLM_BASE_URL not set
    }

    with patch.dict(os.environ, env_vars, clear=True):
        provider = get_llm_provider_from_env()

        # Should fallback to Mock
        assert isinstance(provider, MockLLMProvider)


def test_factory_llamacpp_default_model():
    """Test factory uses default model when not specified."""

    env_vars = {
        "CHAT_LLM_PROVIDER": "llamacpp",
        "CHAT_LLM_BASE_URL": "http://llm:8080/v1"
        # CHAT_LLM_MODEL not set
    }

    with patch.dict(os.environ, env_vars, clear=True):
        provider = get_llm_provider_from_env()

        # Should use default model
        assert isinstance(provider, LlamaCppLLMProvider)
        assert provider.model == "qwen3.5-9b"


def test_factory_llamacpp_strict_false():
    """Test factory creates provider with strict=False."""

    env_vars = {
        "CHAT_LLM_PROVIDER": "llamacpp",
        "CHAT_LLM_BASE_URL": "http://llm:8080/v1",
        "CHAT_LLM_STRICT": "false"
    }

    with patch.dict(os.environ, env_vars, clear=True):
        provider = get_llm_provider_from_env()

        # Verify strict mode
        assert isinstance(provider, LlamaCppLLMProvider)
        assert provider.strict is False


def test_factory_mock_provider():
    """Test factory returns MockLLMProvider when explicitly requested."""

    env_vars = {
        "CHAT_LLM_PROVIDER": "mock"
    }

    with patch.dict(os.environ, env_vars, clear=True):
        provider = get_llm_provider_from_env()

        assert isinstance(provider, MockLLMProvider)


def test_factory_default_is_llamacpp():
    """Test factory defaults to llamacpp when CHAT_LLM_PROVIDER not set."""

    env_vars = {
        "CHAT_LLM_BASE_URL": "http://llm:8080/v1"
    }

    with patch.dict(os.environ, env_vars, clear=True):
        provider = get_llm_provider_from_env()

        # Default should be llamacpp
        assert isinstance(provider, LlamaCppLLMProvider)


def test_factory_unknown_provider():
    """Test factory falls back to Mock for unknown provider."""

    env_vars = {
        "CHAT_LLM_PROVIDER": "unknown_provider"
    }

    with patch.dict(os.environ, env_vars, clear=True):
        provider = get_llm_provider_from_env()

        # Should fallback to Mock
        assert isinstance(provider, MockLLMProvider)


def test_factory_openai_respects_network_flag():
    """Test OpenAI provider respects CHAT_LLM_NETWORK_ENABLED."""

    # Case 1: network disabled
    env_vars = {
        "CHAT_LLM_PROVIDER": "openai_http",
        "CHAT_LLM_NETWORK_ENABLED": "false",
        "CHAT_LLM_STRICT": "false"
    }

    with patch.dict(os.environ, env_vars, clear=True):
        provider = get_llm_provider_from_env()
        assert isinstance(provider, MockLLMProvider)

    # Case 2: network enabled but no API key
    env_vars = {
        "CHAT_LLM_PROVIDER": "openai_http",
        "CHAT_LLM_NETWORK_ENABLED": "true"
        # CHAT_OPENAI_API_KEY not set
    }

    with patch.dict(os.environ, env_vars, clear=True):
        provider = get_llm_provider_from_env()
        assert isinstance(provider, MockLLMProvider)


def test_factory_llamacpp_ignores_network_flag():
    """Test llama.cpp provider ignores CHAT_LLM_NETWORK_ENABLED."""

    env_vars = {
        "CHAT_LLM_PROVIDER": "llamacpp",
        "CHAT_LLM_BASE_URL": "http://llm:8080/v1",
        "CHAT_LLM_NETWORK_ENABLED": "false",  # Should be ignored
        "CHAT_LLM_STRICT": "true"
    }

    with patch.dict(os.environ, env_vars, clear=True):
        provider = get_llm_provider_from_env()

        # Should return LlamaCpp (ignores network flag)
        assert isinstance(provider, LlamaCppLLMProvider)


if __name__ == "__main__":
    # Run tests manually
    print("=" * 60)
    print("Testing LLM Provider Factory")
    print("=" * 60)

    test_factory_llamacpp_provider()
    print("✅ test_factory_llamacpp_provider PASSED")

    test_factory_llamacpp_missing_base_url()
    print("✅ test_factory_llamacpp_missing_base_url PASSED")

    test_factory_llamacpp_missing_base_url_non_strict()
    print("✅ test_factory_llamacpp_missing_base_url_non_strict PASSED")

    test_factory_llamacpp_default_model()
    print("✅ test_factory_llamacpp_default_model PASSED")

    test_factory_llamacpp_strict_false()
    print("✅ test_factory_llamacpp_strict_false PASSED")

    test_factory_mock_provider()
    print("✅ test_factory_mock_provider PASSED")

    test_factory_default_is_llamacpp()
    print("✅ test_factory_default_is_llamacpp PASSED")

    test_factory_unknown_provider()
    print("✅ test_factory_unknown_provider PASSED")

    test_factory_openai_respects_network_flag()
    print("✅ test_factory_openai_respects_network_flag PASSED")

    test_factory_llamacpp_ignores_network_flag()
    print("✅ test_factory_llamacpp_ignores_network_flag PASSED")

    print("\n" + "=" * 60)
    print("✅ All factory tests passed!")
    print("=" * 60)
