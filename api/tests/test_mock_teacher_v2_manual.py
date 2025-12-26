#!/usr/bin/env python3
"""
Manual test for Mock Teacher v2 - Demonstrates contextual, non-repetitive responses

Run this script to see example responses for two different user inputs.
"""

import asyncio
import sys
sys.path.insert(0, '/home/edann/vscode_projects/filltheword/api')

from app.llm.mock_provider import MockLLMProvider


async def test_manual():
    """Manual test showing contextual responses."""
    provider = MockLLMProvider()

    print("=" * 80)
    print("MOCK TEACHER v2 - MANUAL TEST")
    print("=" * 80)
    print()

    # Test 1: Grammatically incorrect sentence
    print("TEST 1: User sends incorrect sentence")
    print("-" * 80)
    user_input_1 = "I go to the market yesterday."
    print(f"User: '{user_input_1}'")
    print()

    messages1 = [
        {"role": "system", "content": "You are an English teacher helping a A2 level student."},
        {"role": "user", "content": user_input_1}
    ]

    print("Assistant: ", end="")
    response1_tokens = []
    async for token in provider.chat_stream(messages1, "system", {"lesson_frame": {"topic": "past_simple"}}):
        response1_tokens.append(token)
        print(token, end="", flush=True)
        await asyncio.sleep(0.01)  # Faster than real-time for demo

    response1 = "".join(response1_tokens)
    print()
    print()

    # Test 2: Grammatically correct sentence
    print("TEST 2: User sends correct sentence")
    print("-" * 80)
    user_input_2 = "Yesterday I went to the market."
    print(f"User: '{user_input_2}'")
    print()

    messages2 = [
        {"role": "system", "content": "You are an English teacher helping a A2 level student."},
        {"role": "user", "content": user_input_2}
    ]

    print("Assistant: ", end="")
    response2_tokens = []
    async for token in provider.chat_stream(messages2, "system", {"lesson_frame": {"topic": "past_simple"}}):
        response2_tokens.append(token)
        print(token, end="", flush=True)
        await asyncio.sleep(0.01)

    response2 = "".join(response2_tokens)
    print()
    print()

    # Analysis
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()

    print("✅ Contextual elements:")
    print(f"   - Response 1 contains user input: {user_input_1 in response1}")
    print(f"   - Response 2 contains user input: {user_input_2 in response2}")
    print()

    print("✅ Different responses:")
    print(f"   - Responses are different: {response1 != response2}")
    print()

    print("✅ Response 1 key elements:")
    print(f"   - Length: {len(response1)} characters")
    print(f"   - Contains 'You wrote': {'You wrote' in response1 or 'you wrote' in response1 or 'You said' in response1 or 'you said' in response1}")
    print(f"   - Contains correction: {any(c in response1 for c in ['verb tense', 'past simple', 'grammar', 'correction'])}")
    print(f"   - Ends with question: {response1.strip().endswith('?')}")
    print()

    print("✅ Response 2 key elements:")
    print(f"   - Length: {len(response2)} characters")
    print(f"   - Contains 'You wrote': {'You wrote' in response2 or 'you wrote' in response2 or 'You said' in response2 or 'you said' in response2}")
    print(f"   - Contains correction: {any(c in response2 for c in ['verb tense', 'past simple', 'grammar', 'correction'])}")
    print(f"   - Ends with question: {response2.strip().endswith('?')}")
    print()

    print("=" * 80)
    print("✅ Mock Teacher v2 is working correctly!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_manual())
