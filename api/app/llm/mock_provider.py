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
    Mock LLM provider v3 for development and testing.

    Returns contextual, coherent responses using unified text analysis.
    All methods are async to match the interface of real providers.
    """

    # Basic stopwords for keyword extraction
    STOPWORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "to", "of", "in", "on", "at", "by", "for", "with", "about", "as",
        "i", "you", "he", "she", "it", "we", "they", "my", "your", "his",
        "her", "its", "our", "their", "this", "that", "these", "those",
        "and", "or", "but", "so", "because", "if", "when", "where", "what",
        "how", "who", "which", "do", "does", "did", "have", "has", "had"
    }

    # Common irregular verbs for error detection
    IRREGULAR_VERBS = {
        "go": "went", "went": "gone",
        "do": "did", "did": "done",
        "have": "had", "had": "had",
        "eat": "ate", "ate": "eaten",
        "write": "wrote", "wrote": "written",
        "take": "took", "took": "taken",
        "make": "made", "made": "made",
        "come": "came", "came": "come"
    }

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

    def _analyze_text(self, text: str, lesson_frame: dict) -> dict:
        """
        Unified text analysis for consistent feedback across methods.

        Extracts keywords, infers topic, detects errors, and generates corrections.
        Uses simple heuristics (no NLP dependencies) for speed and determinism.

        Args:
            text: User's input text
            lesson_frame: Current lesson frame with topic/goal

        Returns:
            Dict with:
            - keywords: List of relevant words from text
            - topic: Inferred grammatical topic
            - detected_errors: List of error dicts with spans
            - correction_text: One-sentence correction
            - rewrite: Improved version using user's keywords
            - follow_up: Follow-up question
        """
        # 1. Extract keywords (remove stopwords, keep words >= 4 chars)
        words = text.lower().replace(".", "").replace(",", "").replace("?", "").split()
        keywords = [w for w in words if w not in self.STOPWORDS and len(w) >= 4][:3]

        # Fallback if no keywords found
        if not keywords:
            keywords = ["practice", "sentence"]

        # 2. Infer topic from text (simple heuristics)
        text_lower = text.lower()

        # Topic inference by keywords
        if any(w in text_lower for w in ["yesterday", "last", "ago", "earlier"]):
            topic = "past_simple"
        elif any(w in text_lower for w in ["tomorrow", "next", "will", "going to"]):
            topic = "future"
        elif any(w in text_lower for w in ["now", "currently", "at the moment"]) or text_lower.strip().endswith("ing"):
            topic = "present_continuous"
        elif any(w in text_lower for w in ["like", "enjoy", "love", "hobbies", "free time"]):
            topic = "hobbies"
        elif any(w in text_lower for w in ["work", "job", "office", "company"]):
            topic = "work"
        elif any(w in text_lower for w in ["weekend", "saturday", "sunday", "holiday"]):
            topic = "weekend_plans"
        else:
            # Use lesson frame topic as fallback
            topic = lesson_frame.get("topic", "getting_started")

        # 3. Detect errors (deterministic based on text)
        detected_errors = []

        # Check for verb tense errors when topic is past_simple
        if topic == "past_simple":
            # Look for common verbs that should be in past tense
            for verb_base, verb_past in self.IRREGULAR_VERBS.items():
                if verb_base in text_lower:
                    # Found base form used in past context
                    idx = text_lower.find(verb_base)
                    detected_errors.append({
                        "type": "verb_tense",
                        "original": verb_base,
                        "correction": verb_past,
                        "span": {"start": idx, "end": idx + len(verb_base)},
                        "explanation": f"Use past tense '{verb_past}' instead of '{verb_base}' for past actions."
                    })
                    break  # Only detect one error per call for simplicity

        # If no errors detected but topic suggests past tense, add a generic one
        if not detected_errors and topic == "past_simple":
            detected_errors.append({
                "type": "time_marker",
                "original": "present tense",
                "correction": "past tense",
                "span": {},
                "explanation": "Remember to use past tense for past events."
            })

        # 4. Generate correction text (uses detected error or generic)
        if detected_errors:
            first_error = detected_errors[0]
            correction_text = first_error["explanation"]
        else:
            correction_text = "Your sentence structure is good. Let's make it even better."

        # 5. Generate rewrite using user's keywords
        # Create a coherent sentence using keywords from user's text
        if keywords:
            main_keyword = keywords[0]
            if topic == "past_simple":
                # Convert to past form if it's a common irregular verb
                verb_past = self.IRREGULAR_VERBS.get(main_keyword, main_keyword + "ed")
                rewrite = f"I {verb_past} {keywords[1] if len(keywords) > 1 else 'there'} yesterday."
            elif topic == "hobbies":
                rewrite = f"I really enjoy {main_keyword}ing in my free time."
            elif topic == "work":
                rewrite = f"I work as a {main_keyword} in a big company."
            else:
                rewrite = f"I {main_keyword} every day."
        else:
            rewrite = "I practiced this yesterday."

        # 6. Generate follow-up question based on topic
        follow_ups = {
            "past_simple": [
                "What did you do next?",
                "Tell me more about it.",
                "How was your experience?"
            ],
            "future": [
                "What are your plans?",
                "Who will you go with?",
                "What do you need to prepare?"
            ],
            "present_continuous": [
                "How long have you been doing that?",
                "What else are you working on?",
                "How is it going?"
            ],
            "hobbies": [
                "How often do you practice?",
                "Do you have any other hobbies?",
                "What do you enjoy most about it?"
            ],
            "work": [
                "What do you like about your job?",
                "What are your responsibilities?",
                "Do you have a busy schedule?"
            ],
            "weekend_plans": [
                "What are your plans for this weekend?",
                "Do you prefer relaxing or being active?",
                "What did you do last weekend?"
            ]
        }

        topic_follow_ups = follow_ups.get(topic, ["Tell me more.", "Can you elaborate?"])
        follow_up = topic_follow_ups[hash(text) % len(topic_follow_ups)]

        return {
            "keywords": keywords,
            "topic": topic,
            "detected_errors": detected_errors,
            "correction_text": correction_text,
            "rewrite": rewrite,
            "follow_up": follow_up
        }

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        generation_config: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Mock streaming chat completion with contextual, coherent responses.

        Uses _analyze_text() to extract keywords and generate consistent feedback.
        Responses are deterministic for testing but vary by input.
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
        analysis = self._analyze_text(last_user_content, lesson_frame)

        # Create stable seed for template selection (varies by content)
        content_hash = sum(ord(c) for c in last_user_content) % 10000
        rng = random.Random(content_hash)

        # Select template deterministically
        template_idx = content_hash % len(self.TEACHER_RESPONSE_TEMPLATES)
        template = self.TEACHER_RESPONSE_TEMPLATES[template_idx]

        # Extract excerpt from user message (first 40 chars max)
        user_excerpt = last_user_content[:40] if len(last_user_content) > 40 else last_user_content

        # Assemble the response using analysis results
        response = template.format(
            user_excerpt=user_excerpt,
            correction=analysis["correction_text"],
            rewrite=analysis["rewrite"],
            topic=analysis["topic"].replace("_", " ")
        )

        # Add follow-up question
        response += " " + analysis["follow_up"]

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
        Mock micro-evaluation of student's draft using unified text analysis.

        Returns stable scores and issues that match what chat_stream would say.
        Uses _analyze_text() to ensure coherence with chat responses.
        """
        # Use unified text analysis
        analysis = self._analyze_text(draft, lesson_frame)

        # Generate pseudo-random but stable scores based on draft content
        score_seed = sum(ord(c) for c in draft) % 100

        # Create LOCAL RNG (does not affect other methods)
        rng = random.Random(score_seed)

        # Base scores with some variation but generally tied to detected errors
        has_errors = len(analysis["detected_errors"]) > 0

        if has_errors:
            grammar_score = 40 + (rng.randint(0, 99) % 30)  # 40-70 (has errors)
            spelling_score = 70 + (rng.randint(0, 99) % 30)  # 70-100
            naturalness_score = 40 + (rng.randint(0, 99) % 40)  # 40-80
            lesson_alignment_score = 50 + (rng.randint(0, 99) % 40)  # 50-90
        else:
            grammar_score = 80 + (rng.randint(0, 99) % 20)  # 80-100 (good)
            spelling_score = 85 + (rng.randint(0, 99) % 15)  # 85-100
            naturalness_score = 70 + (rng.randint(0, 99) % 30)  # 70-100
            lesson_alignment_score = 70 + (rng.randint(0, 99) % 30)  # 70-100

        # Generate issues from detected_errors in analysis
        issues = []

        for error in analysis["detected_errors"][:3]:  # Max 3 issues
            issue = {
                "category": error["type"],
                "title": error.get("original", "Error").capitalize(),
                "explanation": error["explanation"],
                "highlight_spans": [error.get("span", {})] if error.get("span") else [],
                "suggestions": [error.get("correction", "Try again")]
            }
            issues.append(issue)

        # If no detected errors but scores are low, add generic issues
        if not issues and grammar_score < 60:
            issues.append({
                "category": "grammar",
                "title": "Grammar check",
                "explanation": "Review your sentence structure for better clarity.",
                "highlight_spans": [],
                "suggestions": ["Check verb tenses", "Review word order"]
            })

        # Suggested next words based on topic and keywords
        suggestions_by_topic = {
            "past_simple": ["went", "played", "visited", "stayed", "traveled", "watched", "cooked", "studied"],
            "future": ["will", "going to", "plan", "expect", "hope"],
            "present_continuous": ["doing", "working", "playing", "studying", "reading"],
            "hobbies": ["enjoy", "practice", "love", "prefer"],
            "work": ["job", "office", "company", "meetings", "projects"],
            "weekend_plans": ["relax", "visit", "travel", "rest", "explore"]
        }

        topic = analysis["topic"]
        suggestions_pool = suggestions_by_topic.get(topic, ["continue", "practice", "improve"])
        suggested_next_words = rng.sample(suggestions_pool, min(3, len(suggestions_pool)))

        # Micro tip based on performance
        if has_errors:
            micro_tips = [
                f"Good start! {analysis['correction_text']}",
                "Almost there! Check your grammar.",
                f"Nice try! {analysis['correction_text']}",
            ]
        else:
            micro_tips = [
                "Great job! Your sentence is well-structured.",
                "Excellent work! Keep practicing.",
                "You're doing great!",
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
        Mock ghost suggestion (1-6 words) using inferred topic.

        Returns a short continuation based on analyzed topic and last word.
        Uses _analyze_text() for topic inference.
        """
        # Use unified text analysis to get topic
        analysis = self._analyze_text(draft, lesson_frame)
        topic = analysis["topic"]

        # Pseudo-random but deterministic based on draft
        suggestion_seed = sum(ord(c) for c in draft) % 10

        # Create LOCAL RNG (does not affect other methods)
        rng = random.Random(suggestion_seed)

        # Suggestions by topic (contextual)
        suggestions_map = {
            "past_simple": ["went to the", "yesterday", "last week", "visited", "stayed at", "traveled to"],
            "future": ["will go", "going to", "tomorrow", "next week", "plan to"],
            "present_continuous": ["am doing", "is working", "are playing", "currently", "right now"],
            "hobbies": ["enjoy", "practice", "love to", "my favorite"],
            "work": ["at the office", "for my job", "in the company", "during work"],
            "weekend_plans": ["this weekend", "on Saturday", "tomorrow", "next Sunday"],
            "getting_started": ["more", "and then", "also", "next"],
            "default": ["more", "and then", "also", "continue", "next"]
        }

        # Pick suggestion based on topic
        suggestions = suggestions_map.get(topic, suggestions_map["default"])
        ghost_suggestion = rng.choice(suggestions)

        return {
            "ghost_suggestion": ghost_suggestion,
            "reason": f"Based on detected topic: {topic}"
        }
