"""
Test for MockLLMProvider v2 - Contextual, Non-Repetitive Responses

This test ensures that:
1. Responses are contextual (contain user input excerpt)
2. Responses are different for different inputs
3. Responses are deterministic (same input = same output)
"""

import pytest
import asyncio
from app.llm.mock_provider import MockLLMProvider


@pytest.mark.asyncio
async def test_mock_provider_variety():
    """Test that MockLLMProvider generates varied, contextual responses."""
    provider = MockLLMProvider()

    # Test message 1
    messages1 = [
        {"role": "system", "content": "You are a teacher."},
        {"role": "user", "content": "I go to the market yesterday."}
    ]

    # Test message 2 (different input)
    messages2 = [
        {"role": "system", "content": "You are a teacher."},
        {"role": "user", "content": "Yesterday I went to the market."}
    ]

    # Collect full responses
    response1_tokens = []
    response2_tokens = []

    async for token in provider.chat_stream(messages1, "system", {}):
        response1_tokens.append(token)

    async for token in provider.chat_stream(messages2, "system", {}):
        response2_tokens.append(token)

    response1 = "".join(response1_tokens)
    response2 = "".join(response2_tokens)

    # Test 1: Responses are contextual (contain user input excerpt)
    assert "I go to the market yesterday" in response1, \
        f"Response should contain user input excerpt. Got: {response1}"

    assert "Yesterday I went to the market" in response2, \
        f"Response should contain user input excerpt. Got: {response2}"

    # Test 2: Responses are different for different inputs
    assert response1 != response2, \
        "Different inputs should generate different responses"

    # Test 3: Responses contain different corrections/rewrites
    # (they should not just be identical templates with different excerpts)
    # Split by excerpt to compare the rest of the content
    response1_body = response1.replace("I go to the market yesterday", "")
    response2_body = response2.replace("Yesterday I went to the market", "")

    # The bodies should be different (different corrections/rewrites/follow-ups)
    assert response1_body != response2_body, \
        "Response bodies should be different, not just excerpts"

    print(f"\n✅ Response 1: {response1[:100]}...")
    print(f"✅ Response 2: {response2[:100]}...")
    print(f"✅ Responses are contextual and different!")


@pytest.mark.asyncio
async def test_mock_provider_deterministic():
    """Test that MockLLMProvider is deterministic for same input."""
    provider = MockLLMProvider()

    messages = [
        {"role": "system", "content": "You are a teacher."},
        {"role": "user", "content": "I go to the market yesterday."}
    ]

    # Generate response twice
    response1_tokens = []
    response2_tokens = []

    async for token in provider.chat_stream(messages, "system", {}):
        response1_tokens.append(token)

    async for token in provider.chat_stream(messages, "system", {}):
        response2_tokens.append(token)

    response1 = "".join(response1_tokens)
    response2 = "".join(response2_tokens)

    # Same input should produce same output
    assert response1 == response2, \
        "Same input should produce identical output (deterministic)"

    print(f"\n✅ Deterministic test passed: both calls produced same response")


@pytest.mark.asyncio
async def test_mock_provider_contextual_elements():
    """Test that responses contain all required contextual elements."""
    provider = MockLLMProvider()

    messages = [
        {"role": "system", "content": "You are a teacher."},
        {"role": "user", "content": "I play tennis every weekend."}
    ]

    response_tokens = []
    async for token in provider.chat_stream(messages, "system", {}):
        response_tokens.append(token)

    response = "".join(response_tokens)

    # Check for required elements
    assert "I play tennis every weekend" in response, \
        "Response should contain user excerpt"

    # Response should contain a correction (from our template pool)
    # We can't assert exact text, but we can check it has meaningful content
    assert len(response) > 50, "Response should be substantial"

    # Response should end with a follow-up question
    assert "?" in response, "Response should contain a question mark (follow-up)"

    print(f"\n✅ Contextual elements test passed")
    print(f"   Response length: {len(response)} chars")
    print(f"   Contains question mark: {'?' in response}")


if __name__ == "__main__":
    # Run tests manually
    print("=" * 60)
    print("Testing MockLLMProvider v2")
    print("=" * 60)

    asyncio.run(test_mock_provider_variety())
    asyncio.run(test_mock_provider_deterministic())
    asyncio.run(test_mock_provider_contextual_elements())

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
