"""Conversational response helpers for the mock LLM provider."""

import asyncio
from typing import Any, AsyncGenerator, Dict, List

from app.llm.mock_text_analysis import _analyze_text


def _generate_greeting_response(text: str, analysis: dict) -> str:
    """Generate conversational response for greetings."""
    # Random but deterministic greeting responses
    seed = sum(ord(c) for c in text.lower()) % 3

    greetings = [
        f"Hi! I'm doing well, thanks for asking. What would you like to practice today?",
        f"Hello! Great to see you. What's on your mind today?",
        f"Hey there! I'm doing great. What would you like to work on?"
    ]

    return greetings[seed]


def _generate_meta_help_response(text: str, analysis: dict) -> str:
    """Generate helpful response for meta questions like 'what should I do'."""
    # Provide practical guidance
    topic = analysis.get("topic", "general")

    # Generate practical suggestions based on topic
    suggestions = {
        "past_simple": [
            "Try writing about what you did yesterday. Where did you go?",
            "Write about your last weekend. What did you do?",
            "Tell me about a recent trip. Where did you travel to?"
        ],
        "future": [
            "Write about your plans for tomorrow. What will you do?",
            "Tell me about next weekend. What are your plans?",
            "Write about something you want to do soon."
        ],
        "hobbies": [
            "Write about a hobby you enjoy. What do you like to do?",
            "Tell me about your favorite pastime. How often do you practice?",
            "Write about something you do for fun."
        ],
        "work": [
            "Write about your job. What do you do?",
            "Tell me about your work. What's your role?",
            "Write about your last day at work."
        ],
        "general": [
            "Try writing about what you did yesterday. Where did you go?",
            "Write about your favorite hobby. What do you enjoy?",
            "Tell me about your plans for the weekend."
        ]
    }

    topic_suggestions = suggestions.get(topic, suggestions["general"])
    seed = sum(ord(c) for c in text.lower()) % len(topic_suggestions)
    return topic_suggestions[seed]


def _generate_question_response(text: str, analysis: dict) -> str:
    """Generate response for questions."""
    # Check if it's a how/what/where question
    text_lower = text.lower()

    if text_lower.startswith("how"):
        return "That's a good question. Can you give me an example to help me understand better?"
    elif text_lower.startswith("what"):
        return "Interesting question. Tell me more about what you're thinking."
    elif text_lower.startswith("where"):
        return "Good question. Where are you thinking about?"
    elif text_lower.startswith("why"):
        return "I see you're curious. Can you explain the context a bit more?"
    elif text_lower.startswith("when"):
        return "That's a practical question. When are you thinking of?"
    elif text_lower.startswith("who"):
        return "Tell me more about who you're asking about."
    else:
        # Generic question response
        seed = sum(ord(c) for c in text.lower()) % 3
        responses = [
            "Can you tell me more details?",
            "That's interesting. Can you elaborate?",
            "I'd like to hear more about that."
        ]
        return responses[seed]


def _generate_command_response(text: str, analysis: dict) -> str:
    """Generate response for short commands like 'let's go'."""
    text_lower = text.lower()

    # Specific responses for common commands
    if "let's go" in text_lower or "lets go" in text_lower:
        return "Sure! Where would you like to go?"
    elif "ok" in text_lower or "okay" in text_lower:
        return "Great! What would you like to practice?"
    elif "yes" in text_lower:
        return "Perfect! What's next?"
    elif "no" in text_lower:
        return "No problem. What would you prefer instead?"
    else:
        # Generic command acknowledgment
        seed = sum(ord(c) for c in text_lower) % 3
        responses = [
            "Got it! What would you like to do next?",
            "Alright! Tell me more.",
            "Okay, I'm ready. What's on your mind?"
        ]
        return responses[seed]


def _generate_statement_response(text: str, analysis: dict) -> str:
    """Generate conversational response for statements."""
    detected_errors = analysis.get("detected_errors", [])
    has_errors = len(detected_errors) > 0
    topic = analysis.get("topic", "general")
    excerpt = text.strip().rstrip(".?!")

    follow_ups = {
        "past_simple": "Tell me more about it.",
        "future": "What are your plans?",
        "hobbies": "How often do you do that?",
        "work": "What do you like about it?",
        "general": "Can you tell me more?"
    }
    topic_follow_up = follow_ups.get(topic, follow_ups["general"])

    if has_errors:
        correction_text = analysis.get("correction_text", "Good effort.")
        rewrite = analysis.get("rewrite", text)
        return f"You wrote '{excerpt}'. {correction_text} Better: {rewrite} {topic_follow_up}"

    responses_by_topic = {
        "past_simple": [
            "That sounds great! Did you enjoy it?",
            "Interesting! How was it?",
            "Nice! Tell me more about it."
        ],
        "future": [
            "Sounds exciting! Any specific plans?",
            "Great! What are you looking forward to?",
            "That's good. When will you do that?"
        ],
        "hobbies": [
            "That's fun! How often do you practice?",
            "Nice! Do you enjoy it a lot?",
            "Great! What do you like most about it?"
        ],
        "work": [
            "I see. What do you like about your job?",
            "Okay. Is it challenging?",
            "Got it. What do you do exactly?"
        ],
        "general": [
            "I see. Tell me more about that.",
            "That's interesting. Can you elaborate?",
            "Okay. What else would you like to share?"
        ]
    }

    topic_responses = responses_by_topic.get(topic, responses_by_topic["general"])
    seed = sum(ord(c) for c in text.lower()) % len(topic_responses)
    return f"You wrote '{excerpt}'. {topic_responses[seed]}"


async def chat_stream(
    messages: List[Dict[str, str]],
    system_prompt: str,
    generation_config: Dict[str, Any]
) -> AsyncGenerator[str, None]:
    """
    Mock streaming chat completion with conversational, context-aware responses.

    Routes responses by intent (greeting, question, command, statement)
    to provide natural, conversation-first replies.
    """
    # Extract last user message
    user_messages = [m for m in messages if m.get("role") == "user"]
    if not user_messages:
        # Fallback for empty conversation
        last_user_content = "Hello"
    else:
        last_user_content = user_messages[-1].get("content", "Hello")

    # Get lesson frame from config (if available)
    lesson_frame = generation_config.get("lesson_frame", {})

    # Use unified text analysis
    analysis = _analyze_text(last_user_content, lesson_frame)
    intent = analysis.get("intent", "statement")

    # Route by intent to generate appropriate response
    if intent == "greeting":
        response = _generate_greeting_response(last_user_content, analysis)

    elif intent == "question":
        # Check if it's a meta-help question
        text_lower = last_user_content.lower()
        meta_keywords = ["what should", "how can", "help me", "what do", "tell me"]
        is_meta_help = any(kw in text_lower for kw in meta_keywords)

        if is_meta_help:
            response = _generate_meta_help_response(last_user_content, analysis)
        else:
            response = _generate_question_response(last_user_content, analysis)

    elif intent == "short":
        response = _generate_command_response(last_user_content, analysis)

    else:  # statement
        response = _generate_statement_response(last_user_content, analysis)

    # Add appropriate punctuation at the end (single punctuation)
    if not response.endswith((".", "?", "!")):
        # Determine if it's a question or statement
        if "?" in response or response.endswith("?"):
            response = response + "?"
        else:
            response = response + "."

    # Split into tokens and stream
    tokens = response.split()

    # Stream tokens with small delay to simulate real LLM
    for token in tokens:
        await asyncio.sleep(0.05)  # 50ms per token (simulates generation time)
        yield token + " "
