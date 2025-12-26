"""
Test for MockLLMProvider v3 - Contextual, Coherent Responses

This test ensures that:
1. Responses are contextual (contain user input excerpt)
2. Responses are different for different inputs
3. Responses are deterministic (same input = same output)
4. v3: Responses use keywords extracted from user input (not generic)
5. v3: chat_stream and micro_eval are coherent (mention same errors)
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
    print("Testing MockLLMProvider v4")
    print("=" * 60)

    asyncio.run(test_mock_provider_variety())
    asyncio.run(test_mock_provider_deterministic())
    asyncio.run(test_mock_provider_contextual_elements())
    asyncio.run(test_mock_provider_v3_keywords_extraction())
    asyncio.run(test_mock_provider_v3_coherence())
    asyncio.run(test_mock_provider_v3_topic_inference())
    asyncio.run(test_mock_provider_v4_greeting_detection())
    asyncio.run(test_mock_provider_v4_contraction_error())
    asyncio.run(test_mock_provider_v4_question_punctuation())
    asyncio.run(test_mock_provider_v4_rewrite_coherence())

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


# ============================================================================
# v4 Regression Tests: Greeting, Contraction, Autocomplete
# ============================================================================

@pytest.mark.asyncio
async def test_mock_provider_v4_greeting_detection():
    """Test that greetings are detected and handled correctly (v4)."""
    provider = MockLLMProvider()

    # Test 1: Greeting without punctuation
    text1 = "hi, how are you"
    lesson_frame = {}

    analysis1 = provider._analyze_text(text1, lesson_frame)

    # Should detect intent as greeting (or greeting-like)
    assert analysis1["intent"] == "greeting", \
        f"Should detect greeting intent. Got: {analysis1['intent']}"

    # Should detect punctuation/style issue (missing ? for question)
    # Note: "how are you" is a question inside the greeting
    detected_errors = analysis1["detected_errors"]
    assert len(detected_errors) > 0, "Should detect at least one issue"

    # One of the errors should be style or punctuation related
    error_categories = [e.get("category") for e in detected_errors]
    assert "style" in error_categories or "grammar" in error_categories, \
        f"Should have style or grammar issue. Got categories: {error_categories}"

    # Rewrite should be plausible (capitalized, punctuated)
    rewrite1 = analysis1["rewrite"]
    assert rewrite1[0].isupper(), f"Rewrite should be capitalized. Got: {rewrite1}"
    assert rewrite1.endswith((".", "?", "!")), f"Rewrite should end with punctuation. Got: {rewrite1}"

    # Test 2: Greeting with proper punctuation
    text2 = "Hello, how are you?"
    analysis2 = provider._analyze_text(text2, lesson_frame)

    # Should detect as greeting or question
    assert analysis2["intent"] in ["greeting", "question"], \
        f"Should detect greeting/question intent. Got: {analysis2['intent']}"

    # Rewrite should maintain the question mark
    rewrite2 = analysis2["rewrite"]
    assert "?" in rewrite2, f"Rewrite should keep question mark. Got: {rewrite2}"

    print(f"\n✅ Greeting detection test passed")
    print(f"   Text1: '{text1}'")
    print(f"   Intent: {analysis1['intent']}")
    print(f"   Errors: {error_categories}")
    print(f"   Rewrite: '{rewrite1}'")
    print(f"   Text2: '{text2}'")
    print(f"   Rewrite: '{rewrite2}'")


@pytest.mark.asyncio
async def test_mock_provider_v4_contraction_error():
    """Test that contraction errors are detected and corrected (v4)."""
    provider = MockLLMProvider()

    # Test 1: "lets go" without apostrophe
    text1 = "lets go"
    lesson_frame = {}

    analysis1 = provider._analyze_text(text1, lesson_frame)

    # Should detect contraction error
    detected_errors = analysis1["detected_errors"]
    assert len(detected_errors) > 0, "Should detect contraction error"

    # Check for contraction type
    error_types = [e.get("type") for e in detected_errors]
    assert "contraction" in error_types, \
        f"Should detect 'contraction' type. Got types: {error_types}"

    # Category should be grammar
    contraction_error = next(e for e in detected_errors if e.get("type") == "contraction")
    assert contraction_error.get("category") == "grammar", \
        f"Contraction error should be 'grammar' category. Got: {contraction_error.get('category')}"

    # Correction should be "let's"
    assert contraction_error.get("correction") == "let's", \
        f"Correction should be 'let's'. Got: {contraction_error.get('correction')}"

    # Rewrite should apply the correction
    rewrite1 = analysis1["rewrite"]
    assert "let's" in rewrite1.lower(), \
        f"Rewrite should contain 'let's'. Got: {rewrite1}"

    print(f"\n✅ Contraction error test passed")
    print(f"   Text: '{text1}'")
    print(f"   Error types: {error_types}")
    print(f"   Correction: {contraction_error.get('correction')}")
    print(f"   Rewrite: '{rewrite1}'")


@pytest.mark.asyncio
async def test_mock_provider_v4_question_punctuation():
    """Test that questions without ? are detected (v4)."""
    provider = MockLLMProvider()

    # Test 1: Question without question mark
    text1 = "how are you"
    lesson_frame = {}

    analysis1 = provider._analyze_text(text1, lesson_frame)

    # Should detect as question intent
    assert analysis1["intent"] == "question", \
        f"Should detect question intent. Got: {analysis1['intent']}"

    # Should detect punctuation error
    detected_errors = analysis1["detected_errors"]
    assert len(detected_errors) > 0, "Should detect punctuation error"

    # Check for punctuation type
    error_types = [e.get("type") for e in detected_errors]
    assert "punctuation" in error_types, \
        f"Should detect 'punctuation' type. Got types: {error_types}"

    # Category should be style
    punct_error = next(e for e in detected_errors if e.get("type") == "punctuation")
    assert punct_error.get("category") == "style", \
        f"Punctuation error should be 'style' category. Got: {punct_error.get('category')}"

    # Rewrite should add the question mark
    rewrite1 = analysis1["rewrite"]
    assert rewrite1.endswith("?"), \
        f"Rewrite should end with '?'. Got: {rewrite1}"

    # Correction explanation should mention question mark
    assert "question mark" in punct_error.get("explanation", "").lower(), \
        f"Explanation should mention 'question mark'. Got: {punct_error.get('explanation')}"

    print(f"\n✅ Question punctuation test passed")
    print(f"   Text: '{text1}'")
    print(f"   Intent: {analysis1['intent']}")
    print(f"   Error types: {error_types}")
    print(f"   Rewrite: '{rewrite1}'")


@pytest.mark.asyncio
async def test_mock_provider_v4_rewrite_coherence():
    """Test that rewrites are coherent with original text (v4)."""
    provider = MockLLMProvider()

    # Test various inputs
    test_cases = [
        ("hi, how are you", "greeting"),
        ("lets go to the park", "statement"),
        ("how was your weekend", "question"),
        ("i went to the beach yesterday", "statement"),
    ]

    for text, expected_intent in test_cases:
        analysis = provider._analyze_text(text, {})

        # Rewrite should be based on original text
        rewrite = analysis["rewrite"]

        # Rewrite should be capitalized
        assert rewrite[0].isupper(), \
            f"Rewrite should be capitalized for '{text}'. Got: '{rewrite}'"

        # Rewrite should end with proper punctuation
        assert rewrite.endswith((".", "?", "!")), \
            f"Rewrite should end with punctuation for '{text}'. Got: '{rewrite}'"

        # Rewrite should not be generic nonsense like "I keyword every day"
        assert "every day" not in rewrite.lower(), \
            f"Rewrite should not contain generic 'every day' pattern. Got: '{rewrite}'"

        # If there are errors, rewrite should apply corrections
        if analysis["detected_errors"]:
            for error in analysis["detected_errors"]:
                correction = error.get("correction", "")
                if correction:
                    # Rewrite should contain the correction
                    assert correction.lower() in rewrite.lower(), \
                        f"Rewrite should contain correction '{correction}'. Got: '{rewrite}'"

        print(f"   ✅ '{text}' → '{rewrite}'")

    print(f"\n✅ Rewrite coherence test passed")
    print(f"   All {len(test_cases)} test cases passed")



# ============================================================================
# v3 Regression Tests: Coherence and Context
# ============================================================================

@pytest.mark.asyncio
async def test_mock_provider_v3_keywords_extraction():
    """Test that _analyze_text extracts keywords from user input (v3)."""
    provider = MockLLMProvider()

    # Test 1: Extract keywords from sentence
    text1 = "I go to the beach yesterday with friends"
    lesson_frame = {"topic": "past_simple"}

    analysis1 = provider._analyze_text(text1, lesson_frame)

    # Should extract meaningful keywords (not stopwords)
    assert "beach" in analysis1["keywords"] or "yesterday" in analysis1["keywords"], \
        f"Should extract keywords like 'beach' or 'yesterday'. Got: {analysis1['keywords']}"

    # Should infer topic from text
    assert analysis1["topic"] == "past_simple", \
        f"Should infer 'past_simple' topic from 'yesterday'. Got: {analysis1['topic']}"

    # Should detect error (go -> went)
    assert len(analysis1["detected_errors"]) > 0, \
        "Should detect verb tense error for 'go' in past context"

    # Test 2: Different text, different keywords
    text2 = "I work as a teacher in big school"
    analysis2 = provider._analyze_text(text2, {})

    assert "work" in analysis2["keywords"] or "teacher" in analysis2["keywords"], \
        f"Should extract keywords like 'work' or 'teacher'. Got: {analysis2['keywords']}"

    assert analysis2["topic"] == "work", \
        f"Should infer 'work' topic. Got: {analysis2['topic']}"

    print(f"\n✅ Keywords extraction test passed")
    print(f"   Text1 keywords: {analysis1['keywords']}")
    print(f"   Text1 topic: {analysis1['topic']}")
    print(f"   Text2 keywords: {analysis2['keywords']}")
    print(f"   Text2 topic: {analysis2['topic']}")


@pytest.mark.asyncio
async def test_mock_provider_v3_coherence():
    """Test that chat_stream and micro_eval mention the same error (v3)."""
    provider = MockLLMProvider()

    # User message with clear error
    user_text = "I go to the park yesterday"
    messages = [
        {"role": "system", "content": "You are a teacher."},
        {"role": "user", "content": user_text}
    ]

    # Get chat_stream response
    chat_response_tokens = []
    async for token in provider.chat_stream(messages, "system", {}):
        chat_response_tokens.append(token)
    chat_response = "".join(chat_response_tokens)

    # Get micro_eval analysis
    eval_result = await provider.micro_eval(
        context="",
        lesson_frame={},
        draft=user_text,
        student_profile={}
    )

    # Both should mention the same error (verb tense: go -> went)
    # Check chat_stream mentions it
    assert "went" in chat_response.lower() or "past" in chat_response.lower(), \
        f"chat_stream should mention the correction. Got: {chat_response[:200]}"

    # Check micro_eval mentions it
    issues = eval_result["top_issues"]
    assert len(issues) > 0, "micro_eval should detect errors"

    # The issue should be about verb_tense or grammar
    error_types = [issue["category"] for issue in issues]
    assert "verb_tense" in error_types or "grammar" in error_types, \
        f"Should detect verb_tense error. Got types: {error_types}"

    print(f"\n✅ Coherence test passed")
    print(f"   chat_stream mentions correction: {'went' in chat_response.lower()}")
    print(f"   micro_eval issues: {[i['category'] for i in issues]}")


@pytest.mark.asyncio
async def test_mock_provider_v3_topic_inference():
    """Test that autocomplete uses inferred topic (v3)."""
    provider = MockLLMProvider()

    # Test 1: Past simple context
    text1 = "Yesterday I went to"
    result1 = await provider.autocomplete("", {}, text1, {})

    # Suggestion should be past tense related
    suggestion1 = result1["ghost_suggestion"].lower()
    assert "past" in result1["reason"] or "yesterday" in result1["reason"] or \
           any(word in suggestion1 for word in ["went", "visited", "stayed", "traveled"]), \
        f"Suggestion should be past tense related. Got: {suggestion1}, reason: {result1['reason']}"

    # Test 2: Future context
    text2 = "Tomorrow I will"
    result2 = await provider.autocomplete("", {}, text2, {})

    # Suggestion should be future related
    suggestion2 = result2["ghost_suggestion"].lower()
    assert "future" in result2["reason"] or "tomorrow" in result2["reason"] or \
           "will" in suggestion2 or "going to" in suggestion2, \
        f"Suggestion should be future related. Got: {suggestion2}, reason: {result2['reason']}"

    print(f"\n✅ Topic inference test passed")
    print(f"   Text1 suggestion: {result1['ghost_suggestion']} (reason: {result1['reason']})")
    print(f"   Text2 suggestion: {result2['ghost_suggestion']} (reason: {result2['reason']})")
