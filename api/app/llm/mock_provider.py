"""Mock LLM Provider for development (no GPU required)"""

import asyncio
import random
from typing import AsyncGenerator, Dict, Any, List

from app.llm.provider_base import LLMProvider


class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider for development and testing.

    Returns realistic-looking responses without requiring GPU or external API.
    All methods are async to match the interface of real providers.
    """

    # Mock response templates
    TEACHER_RESPONSES = [
        "That's a good attempt! Let me help you with the grammar.",
        "Nice try! Remember that we use past simple for yesterday.",
        "You're getting there! Just check the verb tense.",
        "Good effort! Let's work on that sentence structure.",
        "Almost there! Try using the past tense.",
    ]

    TOKENS_SHORT = [
        "That", "'s", "great", "!", "But", "remember", ",",
        "we", "use", "past", "simple", "for", "yesterday",
        "Can", "you", "try", "again", "?"
    ]

    def __init__(self):
        """Initialize mock provider with random seed for variety."""
        self.random = random.Random(42)  # Fixed seed for consistent tests

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        generation_config: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Mock streaming chat completion.

        Returns a fixed teacher response token-by-token.
        Simulates network latency with small delays.
        """
        # Pick a random response
        response = self.random.choice(self.TEACHER_RESPONSES)

        # Split into tokens (rough approximation)
        tokens = response.split()

        # Stream tokens with small delay to simulate real LLM
        for token in tokens:
            await asyncio.sleep(0.05)  # 50ms per token (simulates generation time)
            yield token + " "

        # Add final punctuation
        if not response.endswith(("!", ".", "?")):
            await asyncio.sleep(0.05)
            yield "."

    async def micro_eval(
        self,
        context: str,
        lesson_frame: Dict[str, Any],
        draft: str,
        student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mock micro-evaluation of student's draft.

        Returns stable scores (avoids big jumps) and 1-3 simple issues.
        Scores are based on draft length and lesson goal (deterministic but realistic).
        """
        # Generate pseudo-random but stable scores based on draft content
        score_seed = sum(ord(c) for c in draft) % 100
        self.random.seed(score_seed)

        # Base scores
        grammar_score = 40 + (score_seed % 60)  # 40-100
        spelling_score = 70 + (score_seed % 30)  # 70-100 (most words are spelled correctly)
        naturalness_score = 30 + (score_seed % 70)  # 30-100
        lesson_alignment_score = 20 + (score_seed % 80)  # 20-100

        # Generate 1-3 simple issues based on scores
        issues = []

        if grammar_score < 60:
            issues.append({
                "category": "grammar",
                "title": "Verb tense",
                "explanation": "Use past simple for past events: 'go' → 'went'",
                "highlight_spans": [{"start": 2, "end": 4}],
                "suggestions": ["went", "traveled", "stayed"]
            })

        if spelling_score < 80:
            issues.append({
                "category": "spelling",
                "title": "Spelling error",
                "explanation": "Check the spelling of this word",
                "highlight_spans": [{"start": 5, "end": 10}],
                "suggestions": ["example", "correct", "practice"]
            })

        if naturalness_score < 50:
            issues.append({
                "category": "style",
                "title": "Sentence structure",
                "explanation": "Try to make the sentence more natural",
                "highlight_spans": [],
                "suggestions": ["Use shorter sentences", "Add time markers"]
            })

        # Suggested next words (2-4 words)
        suggestions_pool = ["went", "played", "visited", "stayed", "traveled", "watched", "cooked", "studied"]
        suggested_next_words = self.random.sample(suggestions_pool, min(3, len(suggestions_pool)))

        # Micro tip
        micro_tips = [
            "Good start! Keep practicing.",
            "Almost there! Check your verb tense.",
            "Nice try! Remember the past tense.",
            "You're doing great! Just fix the spelling.",
        ]
        micro_tip = self.random.choice(micro_tips)

        return {
            "grammar_score": float(grammar_score),
            "spelling_score": float(spelling_score),
            "naturalness_score": float(naturalness_score),
            "lesson_alignment_score": float(lesson_alignment_score),
            "top_issues": issues[:3],  # Max 3 issues
            "suggested_next_words": suggested_next_words,
            "micro_tip": micro_tip
        }

    async def autocomplete(
        self,
        context: str,
        lesson_frame: Dict[str, Any],
        draft: str,
        student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mock ghost suggestion (1-6 words).

        Returns a short continuation based on lesson goal.
        """
        # Pseudo-random but deterministic based on draft
        suggestion_seed = sum(ord(c) for c in draft) % 10
        self.random.seed(suggestion_seed)

        suggestions_map = {
            "past_simple": ["went to the", "played", "visited", "stayed at"],
            "present_continuous": ["am doing", "is working", "are playing"],
            "articles": ["the", "a", "an", "the new"],
            "default": ["more", "and then", "also", "next"]
        }

        # Get learning goal from lesson frame
        learning_goal = lesson_frame.get("learning_goal", "default")

        # Pick suggestion based on goal
        suggestions = suggestions_map.get(learning_goal, suggestions_map["default"])
        ghost_suggestion = self.random.choice(suggestions)

        return {
            "ghost_suggestion": ghost_suggestion,
            "reason": f"Based on lesson goal: {learning_goal}"
        }
