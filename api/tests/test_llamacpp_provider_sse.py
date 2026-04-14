"""
Test LlamaCppLLMProvider with MockTransport (no network required)

Tests:
- SSE streaming parsing
- Strict mode error handling
- generation_config filtering
"""

import pytest
import httpx
import json
from app.llm.llamacpp_provider import LlamaCppLLMProvider


@pytest.mark.asyncio
async def test_llamacpp_provider_chat_stream_sse():
    """Test llama.cpp provider SSE parsing with MockTransport."""

    # Mock SSE handler
    def handler(request):
        # Verify request
        assert request.method == "POST"
        assert "/chat/completions" in request.url.path

        # Parse request body
        payload = json.loads(request.content)
        assert payload["model"] == "gemma-4-e4b-it"
        assert payload["stream"] is True
        assert "lesson_frame" not in payload  # Should be filtered

        # Return SSE stream
        return httpx.Response(
            200,
            content=b'''data: {"choices":[{"delta":{"content":"Hello"}}]}

data: {"choices":[{"delta":{"content":" world"}}]}

data: [DONE]

''',
            headers={"Content-Type": "text/event-stream"}
        )

    # Create provider with MockTransport
    transport = httpx.MockTransport(handler)
    provider = LlamaCppLLMProvider(
        base_url="http://test:8080/v1",
        model="gemma-4-e4b-it",
        timeout=60
    )
    provider.client = httpx.AsyncClient(transport=transport)

    # Test chat_stream
    messages = [{"role": "user", "content": "hi"}]
    system_prompt = "You are a tutor."
    generation_config = {
        "temperature": 0.7,
        "max_tokens": 100,
        "lesson_frame": {"topic": "test"}  # Should be filtered
    }

    tokens = []
    async for token in provider.chat_stream(messages, system_prompt, generation_config):
        tokens.append(token)

    # Verify
    assert "".join(tokens) == "Hello world"


@pytest.mark.asyncio
async def test_llamacpp_provider_filters_generation_config():
    """Test that generation_config is filtered (lesson_frame removed)."""

    filtered_config = None

    def handler(request):
        nonlocal filtered_config
        filtered_config = json.loads(request.content)

        # Should NOT contain lesson_frame
        assert "lesson_frame" not in filtered_config
        # Should contain standard params
        assert "temperature" in filtered_config
        assert "max_tokens" in filtered_config

        return httpx.Response(
            200,
            content=b'data: [DONE]\n\n',
            headers={"Content-Type": "text/event-stream"}
        )

    transport = httpx.MockTransport(handler)
    provider = LlamaCppLLMProvider(
        base_url="http://test:8080/v1",
        model="gemma-4-e4b-it"
    )
    provider.client = httpx.AsyncClient(transport=transport)

    messages = [{"role": "user", "content": "test"}]
    system_prompt = "You are a tutor."
    generation_config = {
        "temperature": 0.7,
        "max_tokens": 100,
        "top_p": 0.9,
        "lesson_frame": {"topic": "past_simple"},  # Should be filtered
        "student_profile": {"level": "A2"}  # Should be filtered
    }

    # Consume stream (will be empty)
    async for _ in provider.chat_stream(messages, system_prompt, generation_config):
        pass

    # Verify filtered config
    assert "lesson_frame" not in filtered_config
    assert "student_profile" not in filtered_config
    assert filtered_config["temperature"] == 0.7
    assert filtered_config["max_tokens"] == 100


@pytest.mark.asyncio
async def test_llamacpp_provider_strict_mode_raises():
    """Test strict mode raises exception on error (no fallback)."""

    # Mock handler that returns error
    def handler(request):
        return httpx.Response(500, content=b"Internal Server Error")

    transport = httpx.MockTransport(handler)
    provider = LlamaCppLLMProvider(
        base_url="http://test:8080/v1",
        model="gemma-4-e4b-it",
        strict=True  # STRICT MODE
    )
    provider.client = httpx.AsyncClient(transport=transport)

    messages = [{"role": "user", "content": "test"}]
    system_prompt = "You are a tutor."
    generation_config = {"temperature": 0.7}

    # Should raise exception (not fallback to Mock)
    with pytest.raises(httpx.HTTPError):
        async for _ in provider.chat_stream(messages, system_prompt, generation_config):
            pass


@pytest.mark.asyncio
async def test_llamacpp_provider_non_strict_fallback():
    """Test non-strict mode falls back to Mock on error."""

    # Mock handler that returns error
    def handler(request):
        return httpx.Response(500, content=b"Internal Server Error")

    transport = httpx.MockTransport(handler)
    provider = LlamaCppLLMProvider(
        base_url="http://test:8080/v1",
        model="gemma-4-e4b-it",
        strict=False  # NON-STRICT
    )
    provider.client = httpx.AsyncClient(transport=transport)

    messages = [{"role": "user", "content": "test"}]
    system_prompt = "You are a tutor."
    generation_config = {"temperature": 0.7}

    # Should fallback to Mock (no exception)
    tokens = []
    async for token in provider.chat_stream(messages, system_prompt, generation_config):
        tokens.append(token)

    # Should return Mock response (not empty)
    assert len(tokens) > 0


@pytest.mark.asyncio
async def test_llamacpp_provider_micro_eval_heuristic():
    """Test micro_eval uses heuristic (not MockLLMProvider directly)."""
    provider = LlamaCppLLMProvider(
        base_url="http://test:8080/v1",
        model="gemma-4-e4b-it"
    )

    result = await provider.micro_eval(
        context="",
        lesson_frame={},
        draft="I go to market yesterday",
        student_profile={}
    )

    # Should return heuristic result (with issues)
    assert "grammar_score" in result
    assert "spelling_score" in result
    assert "top_issues" in result


@pytest.mark.asyncio
async def test_llamacpp_provider_autocomplete_heuristic():
    """Test autocomplete uses heuristic (not MockLLMProvider directly)."""
    provider = LlamaCppLLMProvider(
        base_url="http://test:8080/v1",
        model="gemma-4-e4b-it"
    )

    result = await provider.autocomplete(
        context="",
        lesson_frame={},
        draft="Yesterday I went",
        student_profile={}
    )

    # Should return heuristic result
    assert "ghost_suggestion" in result
    assert "reason" in result


if __name__ == "__main__":
    # Run tests manually
    import asyncio

    print("=" * 60)
    print("Testing LlamaCppLLMProvider (MockTransport)")
    print("=" * 60)

    asyncio.run(test_llamacpp_provider_chat_stream_sse())
    print("✅ test_llamacpp_provider_chat_stream_sse PASSED")

    asyncio.run(test_llamacpp_provider_filters_generation_config())
    print("✅ test_llamacpp_provider_filters_generation_config PASSED")

    asyncio.run(test_llamacpp_provider_strict_mode_raises())
    print("✅ test_llamacpp_provider_strict_mode_raises PASSED")

    asyncio.run(test_llamacpp_provider_non_strict_fallback())
    print("✅ test_llamacpp_provider_non_strict_fallback PASSED")

    asyncio.run(test_llamacpp_provider_micro_eval_heuristic())
    print("✅ test_llamacpp_provider_micro_eval_heuristic PASSED")

    asyncio.run(test_llamacpp_provider_autocomplete_heuristic())
    print("✅ test_llamacpp_provider_autocomplete_heuristic PASSED")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
