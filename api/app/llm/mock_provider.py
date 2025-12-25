"""Mock LLM Provider v2 for development (no GPU required)

Improvements:
- Contextual responses based on user input
- No repetitive responses (local RNG, not shared)
- Deterministic for testing (hash-based seeding)
- Larger template pool (30+ responses)
"""

import asyncio
import random
from typing import AsyncGenerator, Dict, Any, List

from app.llm.provider_base import LLMProvider


class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider v2 for development and testing.

    Returns contextual, non-repetitive responses without requiring GPU.
    All methods are async to match the interface of real providers.
    """

    # 30+ contextual teacher response templates
    TEACHER_RESPONSE_TEMPLATES = [
        # Praising + showing what user wrote + correction + follow-up
        "Great effort! You wrote: '{user_excerpt}'. Let me help you with the correction. {correction} Try this structure: {rewrite}. Can you practice this pattern?",
        "Nice try! Your sentence was '{user_excerpt}'. {correction} Here's a better version: {rewrite}. Would you like to try another example?",
        "Good start! I noticed you wrote '{user_excerpt}'. {correction} A more natural way to say it: {rewrite}. Ready for the next challenge?",
        "Almost there! You said '{user_excerpt}'. {correction} Remember: {rewrite}. Let's practice {topic} some more!",
        "I like your attempt! '{user_excerpt}' is close. {correction} Try saying it like this: {rewrite}. How does that sound?",
        "You're on the right track! For '{user_excerpt}', {correction} Better: {rewrite}. Can you make a similar sentence?",
        "Well done! '{user_excerpt}' shows you're trying. {correction} Native speakers would say: {rewrite}. Want to try again?",
        "Good practice! You wrote '{user_excerpt}'. {correction} Here's the corrected form: {rewrite}. Let's continue with {topic}!",
        "Nice work! I see what you mean with '{user_excerpt}'. {correction} The standard way is: {rewrite}. Shall we try another?",
        "Keep it up! '{user_excerpt}' needs a small fix. {correction} Use this structure: {rewrite}. Ready for more practice?",
        "Excellent attempt! '{user_excerpt}' conveys your idea. {correction} More natural: {rewrite}. Let's explore {topic} further!",
        "You're improving! For '{user_excerpt}', {correction} Remember this pattern: {rewrite}. Can you apply it to a new sentence?",
        "Great job practicing! '{user_excerpt}' is almost perfect. {correction} Just remember: {rewrite}. Want to try {topic} again?",
        "I understand your message '{user_excerpt}'. {correction} Here's how to express it: {rewrite}. Let's work on {topic}!",
        "Good thinking! '{user_excerpt}' makes sense. {correction} A common phrase is: {rewrite}. Can you repeat after me?",
        "You're doing great! '{user_excerpt}' shows progress. {correction} Try this version: {rewrite}. Shall we move to {topic}?",
        "Nice sentence! '{user_excerpt}' needs adjustment. {correction} Native speakers say: {rewrite}. Ready for another example?",
        "Well attempted! '{user_excerpt}' communicates well. {correction} For better accuracy: {rewrite}. Let's practice {topic}!",
        "Keep practicing! '{user_excerpt}' is a good start. {correction} Improve it with: {rewrite}. Can you make your own example?",
        "You're getting better! '{user_excerpt}' demonstrates effort. {correction} Consider saying: {rewrite}. How about we try {topic}?",
        "Excellent! '{user_excerpt}' shows you're engaged. {correction} Polished version: {rewrite}. Let's continue with {topic}!",
        "Good job! '{user_excerpt}' is understandable. {correction} To sound more natural: {rewrite}. Want to practice similar sentences?",
        "Nice effort! You said '{user_excerpt}'. {correction} Correct form: {rewrite}. Can you identify the pattern?",
        "You're learning! '{user_excerpt}' needs refinement. {correction} Try this phrasing: {rewrite}. Shall we explore {topic} more?",
        "Well done! '{user_excerpt}' captures the meaning. {correction} Standard English: {rewrite}. Ready for another challenge?",
        "Great progress! '{user_excerpt}' is getting there. {correction} Remember to use: {rewrite}. Let's practice {topic}!",
        "You're on fire! '{user_excerpt}' shows enthusiasm. {correction} Better expression: {rewrite}. Can you create your own?",
        "I appreciate your effort with '{user_excerpt}'. {correction} Here's a correction: {rewrite}. Want to try {topic} again?",
        "Nice sentence structure! '{user_excerpt}' flows well. {correction} Small fix needed: {rewrite}. Let's continue practicing!",
        "You're trying hard! '{user_excerpt}' demonstrates that. {correction} Native speakers prefer: {rewrite}. Shall we try {topic}?",
        "Good work! '{user_excerpt}' is almost correct. {correction} The proper way: {rewrite}. Can you apply this rule?",
        "Keep it up! '{user_excerpt}' needs minor adjustment. {correction} Remember: {rewrite}. Let's explore {topic} further!",
    ]

    # Correction templates
    CORRECTIONS = [
        "pay attention to the verb tense.",
        "use the past simple form for past actions.",
        "check the subject-verb agreement.",
        "remember to use articles correctly.",
        "be careful with word order.",
        "use the correct preposition.",
        "mind the spelling of this word.",
        "use the present continuous for ongoing actions.",
        "add the necessary time marker.",
        "check if you need 'a' or 'an'.",
        "use 'some' or 'any' correctly.",
        "remember the irregular verb form.",
        "use the comparative form properly.",
        "add the missing auxiliary verb.",
        "check your sentence structure.",
    ]

    # Rewrite templates
    REWRITES = [
        "I went to the {place} yesterday.",
        "I {verb}ed there last week.",
        "She is {verb}ing right now.",
        "They {verb}ed every day.",
        "We are going to the {place}.",
        "He {verb}s very well.",
        "I have been {verb}ing for two hours.",
        "She {verb}ed her homework.",
        "We enjoy {verb}ing on weekends.",
        "I will {verb} tomorrow.",
        "The {noun} is very {adjective}.",
        "She has a {adjective} {noun}.",
        "They were {verb}ing all afternoon.",
        "I was {verb}ing when you called.",
        "He can {verb} very fast.",
    ]

    # Follow-up questions by topic
    FOLLOW_UPS = {
        "weekend_plans": [
            "What are your plans for next weekend?",
            "Do you prefer relaxing or being active on weekends?",
            "Tell me about your last weekend.",
        ],
        "getting_started": [
            "How are you feeling today?",
            "What brings you here to practice?",
            "Do you enjoy learning English?",
        ],
        "past_simple": [
            "What did you do yesterday?",
            "Tell me about your last vacation.",
            "Describe your childhood memory.",
        ],
        "daily_routine": [
            "What time do you usually wake up?",
            "Describe your morning routine.",
            "What do you do in the evenings?",
        ],
        "hobbies": [
            "What do you like to do in your free time?",
            "Do you have any favorite hobbies?",
            "Tell me about your interests.",
        ],
        "default": [
            "Can you tell me more?",
            "What else would you like to practice?",
            "How comfortable are you with this topic?",
        ]
    }

    def __init__(self):
        """Initialize mock provider."""
        # NOTE: We don't use self.random anymore to avoid cross-method interference
        pass

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        generation_config: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Mock streaming chat completion with contextual responses.

        Generates a response based on the last user message.
        Uses deterministic seeding for testability.
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
        topic = lesson_frame.get("topic", "getting_started")

        # Create stable seed from user content (deterministic but varied by input)
        # Use sum of char codes as a simple hash
        content_hash = sum(ord(c) for c in last_user_content) % 10000

        # Create local RNG for this call (isolated from other methods)
        rng = random.Random(content_hash)

        # Select templates deterministically based on content hash
        template_idx = content_hash % len(self.TEACHER_RESPONSE_TEMPLATES)
        template = self.TEACHER_RESPONSE_TEMPLATES[template_idx]

        correction_idx = content_hash % len(self.CORRECTIONS)
        correction = self.CORRECTIONS[correction_idx]

        rewrite_idx = (content_hash * 2) % len(self.REWRITES)
        rewrite_template = self.REWRITES[rewrite_idx]

        # Generate rewrite with simple placeholders
        place = ["market", "park", "beach", "school", "home"][content_hash % 5]
        verb = ["go", "play", "study", "work", "cook"][content_hash % 5]
        noun = ["book", "movie", "car", "house", "food"][content_hash % 5]
        adjective = ["good", "big", "small", "beautiful", "interesting"][content_hash % 5]

        rewrite = rewrite_template.format(
            place=place,
            verb=verb,
            noun=noun,
            adjective=adjective
        )

        # Get follow-up based on topic
        follow_ups = self.FOLLOW_UPS.get(topic, self.FOLLOW_UPS["default"])
        follow_up_idx = (content_hash * 3) % len(follow_ups)
        follow_up = follow_ups[follow_up_idx]

        # Extract excerpt from user message (first 40 chars max)
        user_excerpt = last_user_content[:40] if len(last_user_content) > 40 else last_user_content

        # Assemble the response
        response = template.format(
            user_excerpt=user_excerpt,
            correction=correction,
            rewrite=rewrite,
            topic=topic.replace("_", " ")
        )

        # Add follow-up question
        response += " " + follow_up

        # Split into tokens and stream
        tokens = response.split()

        # Stream tokens with small delay to simulate real LLM
        for token in tokens:
            await asyncio.sleep(0.05)  # 50ms per token (simulates generation time)
            yield token + " "

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
        Uses LOCAL RNG to avoid affecting other methods.
        """
        # Generate pseudo-random but stable scores based on draft content
        score_seed = sum(ord(c) for c in draft) % 100

        # Create LOCAL RNG (does not affect other methods)
        rng = random.Random(score_seed)

        # Base scores
        grammar_score = 40 + (rng.randint(0, 99) % 60)  # 40-100
        spelling_score = 70 + (rng.randint(0, 99) % 30)  # 70-100
        naturalness_score = 30 + (rng.randint(0, 99) % 70)  # 30-100
        lesson_alignment_score = 20 + (rng.randint(0, 99) % 80)  # 20-100

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
        suggested_next_words = rng.sample(suggestions_pool, min(3, len(suggestions_pool)))

        # Micro tip
        micro_tips = [
            "Good start! Keep practicing.",
            "Almost there! Check your verb tense.",
            "Nice try! Remember the past tense.",
            "You're doing great! Just fix the spelling.",
        ]
        micro_tip = rng.choice(micro_tips)

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
        Uses LOCAL RNG to avoid affecting other methods.
        """
        # Pseudo-random but deterministic based on draft
        suggestion_seed = sum(ord(c) for c in draft) % 10

        # Create LOCAL RNG (does not affect other methods)
        rng = random.Random(suggestion_seed)

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
        ghost_suggestion = rng.choice(suggestions)

        return {
            "ghost_suggestion": ghost_suggestion,
            "reason": f"Based on lesson goal: {learning_goal}"
        }
