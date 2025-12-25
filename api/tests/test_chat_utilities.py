"""
Test for Chat Endpoint Utilities

This test ensures that:
1. _sanitize_assistant_response removes quoted user simulation
2. _sanitize_assistant_response truncates at role labels
3. _sanitize_assistant_response handles edge cases
"""

import sys
import os

# Add parent directory to path to import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api.api_v1.endpoints.chat import _sanitize_assistant_response


def test_sanitize_removes_quoted_user_simulation():
    """Test that quoted paragraphs at the end are removed."""
    # Case 1: Quoted text after blank line
    response1 = "That's great! How was your experience?\n\n\"I went to the beach and it was fun.\""
    sanitized1 = _sanitize_assistant_response(response1)

    assert "I went to the beach" not in sanitized1, \
        f"Should remove quoted user simulation. Got: {sanitized1}"
    assert sanitized1 == "That's great! How was your experience?", \
        f"Should keep only assistant response. Got: {sanitized1}"

    # Case 2: Multiple quoted paragraphs
    response2 = "Nice! What did you do?\n\n\"I played tennis.\"\n\n\"It was very fun.\""
    sanitized2 = _sanitize_assistant_response(response2)

    assert "I played tennis" not in sanitized2, \
        f"Should remove all quoted paragraphs. Got: {sanitized2}"
    assert sanitized2 == "Nice! What did you do?", \
        f"Should keep only assistant response. Got: {sanitized2}"

    print(f"\n✅ Quoted user simulation removal test passed")
    print(f"   Input 1: '{response1}'")
    print(f"   Output 1: '{sanitized1}'")
    print(f"   Input 2: '{response2}'")
    print(f"   Output 2: '{sanitized2}'")


def test_sanitize_truncates_at_role_labels():
    """Test that text after role labels is removed."""
    # Case 1: User: label
    response1 = "That's interesting! Tell me more.\nUser: I went to the park yesterday."
    sanitized1 = _sanitize_assistant_response(response1)

    assert "I went to the park" not in sanitized1, \
        f"Should truncate at 'User:'. Got: {sanitized1}"
    assert sanitized1 == "That's interesting! Tell me more.", \
        f"Should keep only text before role label. Got: {sanitized1}"

    # Case 2: STUDENT: label (uppercase)
    response2 = "Great question!\nSTUDENT: I don't understand."
    sanitized2 = _sanitize_assistant_response(response2)

    assert "I don't understand" not in sanitized2, \
        f"Should truncate at 'STUDENT:'. Got: {sanitized2}"
    assert sanitized2 == "Great question!", \
        f"Should keep only text before role label. Got: {sanitized2}"

    # Case 3: Student: label (mixed case)
    response3 = "Hello! How are you?\nStudent: I'm fine, thank you."
    sanitized3 = _sanitize_assistant_response(response3)

    assert "I'm fine" not in sanitized3, \
        f"Should truncate at 'Student:'. Got: {sanitized3}"
    assert sanitized3 == "Hello! How are you?", \
        f"Should keep only text before role label. Got: {sanitized3}"

    print(f"\n✅ Role label truncation test passed")
    print(f"   Input 1: '{response1}'")
    print(f"   Output 1: '{sanitized1}'")
    print(f"   Input 2: '{response2}'")
    print(f"   Output 2: '{sanitized2}'")
    print(f"   Input 3: '{response3}'")
    print(f"   Output 3: '{sanitized3}'")


def test_sanitize_combined_patterns():
    """Test that both quoted text and role labels are handled."""
    # Case 1: Both quoted text and role label (should handle role label first)
    response1 = "Nice day!\n\n\"It's sunny.\"\nUser: Yes, very sunny."
    sanitized1 = _sanitize_assistant_response(response1)

    # Should truncate at User: before quoted text processing
    assert "Yes, very sunny" not in sanitized1, \
        f"Should truncate at role label. Got: {sanitized1}"

    # Case 2: Role label followed by quoted text
    response2 = "Tell me more.\nStudent: \"I like tennis.\""
    sanitized2 = _sanitize_assistant_response(response2)

    assert "I like tennis" not in sanitized2, \
        f"Should truncate at role label. Got: {sanitized2}"
    assert sanitized2 == "Tell me more.", \
        f"Should keep only assistant response. Got: {sanitized2}"

    print(f"\n✅ Combined patterns test passed")
    print(f"   Input 1: '{response1}'")
    print(f"   Output 1: '{sanitized1}'")
    print(f"   Input 2: '{response2}'")
    print(f"   Output 2: '{sanitized2}'")


def test_sanitize_edge_cases():
    """Test edge cases and normal responses."""
    # Case 1: Clean response (no sanitization needed)
    response1 = "That's great! How was your experience?"
    sanitized1 = _sanitize_assistant_response(response1)

    assert sanitized1 == response1, \
        f"Clean response should pass through unchanged. Got: {sanitized1}"

    # Case 2: Empty response
    response2 = ""
    sanitized2 = _sanitize_assistant_response(response2)

    assert sanitized2 == "", \
        f"Empty response should remain empty. Got: '{sanitized2}'"

    # Case 3: Response with quotes in middle (not at end)
    response3 = 'He said "hello" and then left.'
    sanitized3 = _sanitize_assistant_response(response3)

    assert sanitized3 == response3, \
        f"Quotes in middle should not be removed. Got: {sanitized3}"

    # Case 4: Response with normal quotes but no blank line before
    response4 = 'The word is "important" for learning.'
    sanitized4 = _sanitize_assistant_response(response4)

    assert sanitized4 == response4, \
        f"Quotes without blank line should not trigger removal. Got: {sanitized4}"

    print(f"\n✅ Edge cases test passed")
    print(f"   Clean response: '{response1}' → '{sanitized1}'")
    print(f"   Empty response: '{response2}' → '{sanitized2}'")
    print(f"   Quotes in middle: '{response3}' → '{sanitized3}'")
    print(f"   Normal quotes: '{response4}' → '{sanitized4}'")


def test_sanitize_multiline_responses():
    """Test responses with multiple lines."""
    # Case 1: Multiline assistant response followed by user simulation
    response1 = """That's interesting!
Can you tell me more about it?

"I went to the beach with my family.
We had a great time playing in the sand."
"""
    sanitized1 = _sanitize_assistant_response(response1)

    assert "I went to the beach" not in sanitized1, \
        f"Should remove quoted multiline user simulation. Got: {sanitized1}"
    assert "Tell me more about it?" in sanitized1, \
        f"Should keep assistant's multiline response. Got: {sanitized1}"

    # Case 2: Assistant response with multiple paragraphs, no user sim
    response2 = """Hello! How are you today?
I hope you are having a great time learning English.

Do you have any questions for me?"""

    sanitized2 = _sanitize_assistant_response(response2)

    assert sanitized2 == response2, \
        f"Clean multiline response should pass through unchanged. Got: {sanitized2}"

    print(f"\n✅ Multiline responses test passed")
    print(f"   Input 1 (multiline with sim):\n{response1}")
    print(f"   Output 1:\n{sanitized1}")
    print(f"   Input 2 (clean multiline):\n{response2}")
    print(f"   Output 2:\n{sanitized2}")


if __name__ == "__main__":
    # Run tests manually
    print("=" * 60)
    print("Testing Chat Endpoint Utilities")
    print("=" * 60)

    test_sanitize_removes_quoted_user_simulation()
    test_sanitize_truncates_at_role_labels()
    test_sanitize_combined_patterns()
    test_sanitize_edge_cases()
    test_sanitize_multiline_responses()

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
