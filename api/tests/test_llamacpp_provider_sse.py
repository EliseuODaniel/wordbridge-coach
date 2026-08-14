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
async def test_llamacpp_provider_micro_eval_uses_structured_output():
    """Test micro_eval requests schema-constrained JSON and parses it."""
    def handler(request):
        payload = json.loads(request.content)
        assert payload["response_format"]["type"] == "json_schema"
        schema_config = payload["response_format"]["json_schema"]
        assert schema_config["name"] == "DraftEvaluationPayload"
        assert schema_config["strict"] is True
        assert schema_config["schema"]["type"] == "object"
        assert schema_config["schema"]["additionalProperties"] is False
        assert set(schema_config["schema"]["required"]) == set(
            schema_config["schema"]["properties"]
        )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "grammar_score": 84,
                                    "spelling_score": 96,
                                    "naturalness_score": 78,
                                    "lesson_alignment_score": 88,
                                    "top_issues": [
                                        {
                                            "category": "grammar",
                                            "title": "Verb tense",
                                            "explanation": "Use the past form.",
                                            "highlight_text": "go",
                                            "suggestions": ["went"],
                                        }
                                    ],
                                    "suggested_next_words": ["to"],
                                    "micro_tip": "Check the verb after 'yesterday'.",
                                    "self_check_prompt": "What should happen to the verb in a past-time sentence?",
                                    "encouragement": "Your idea is clear; now refine the verb.",
                                    "topic": "travel",
                                    "intent": "past_experience",
                                    "rewrite": "I went to market yesterday",
                                }
                            )
                        }
                    }
                ]
            },
        )

    provider = LlamaCppLLMProvider(
        base_url="http://test:8080/v1",
        model="gemma-4-e4b-it"
    )
    provider.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    result = await provider.micro_eval(
        context="",
        lesson_frame={},
        draft="I go to market yesterday",
        student_profile={}
    )

    assert result["grammar_score"] == 84
    assert result["top_issues"][0]["highlight_text"] == "go"
    assert result["self_check_prompt"] is not None


@pytest.mark.asyncio
async def test_llamacpp_provider_autocomplete_uses_structured_output():
    """Test autocomplete requests schema-constrained JSON and parses it."""
    def handler(request):
        payload = json.loads(request.content)
        assert payload["response_format"]["type"] == "json_schema"
        assert payload["response_format"]["json_schema"]["name"] == "AutocompletePayload"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "ghost_suggestion": "to the park",
                                    "reason": "Keeps the learner moving without finishing the whole sentence.",
                                }
                            )
                        }
                    }
                ]
            },
        )

    provider = LlamaCppLLMProvider(
        base_url="http://test:8080/v1",
        model="gemma-4-e4b-it"
    )
    provider.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    result = await provider.autocomplete(
        context="",
        lesson_frame={},
        draft="Yesterday I went",
        student_profile={}
    )

    assert result["ghost_suggestion"] == "to the park"
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

    asyncio.run(test_llamacpp_provider_micro_eval_uses_structured_output())
    print("✅ test_llamacpp_provider_micro_eval_uses_structured_output PASSED")

    asyncio.run(test_llamacpp_provider_autocomplete_uses_structured_output())
    print("✅ test_llamacpp_provider_autocomplete_uses_structured_output PASSED")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
