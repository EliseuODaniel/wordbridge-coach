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
        Unified text analysis v4 for consistent, plausible feedback.

        Detects intent (greeting, question, statement), specific errors
        (punctuation, contraction, agreement), and generates minimal rewrites.

        Args:
            text: User's input text
            lesson_frame: Current lesson frame with topic/goal

        Returns:
            Dict with keywords, intent, detected_errors, correction, rewrite, follow_up
        """
        text_lower = text.lower().strip()
        text_original = text  # Keep original for rewrite generation

        # ============================================================================
        # 1. Intent Detection
        # ============================================================================
        intent = "statement"

        # Greeting patterns
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
        if any(text_lower.startswith(g) for g in greetings):
            intent = "greeting"
        # Question patterns (starts with wh- or ends with ?)
        elif any(text_lower.startswith(q) for q in ["how", "what", "where", "why", "when", "who", "which", "is", "are", "do", "does", "can"]):
            intent = "question"
        elif text_lower.endswith("?"):
            intent = "question"
        # Imperative/short patterns
        elif len(text_lower.split()) <= 3:
            intent = "short"

        # ============================================================================
        # 2. Error Detection (prioritize specific errors)
        # ============================================================================
        detected_errors = []

        # 2.1. Punctuation: questions should end with ?
        if intent == "question" and not text_original.endswith("?"):
            detected_errors.append({
                "type": "punctuation",
                "category": "style",
                "original": text_original,
                "correction": text_original + "?",
                "span": {},  # No specific span for missing punctuation
                "explanation": "Questions should end with a question mark."
            })

        # 2.2. Contraction: "lets go" → "Let's go"
        if "lets go" in text_lower or " let's " in text_lower:
            idx = text_lower.find("lets")
            if idx >= 0:
                detected_errors.append({
                    "type": "contraction",
                    "category": "grammar",
                    "original": "lets",
                    "correction": "let's",
                    "span": {"start": idx, "end": idx + 4},
                    "explanation": "Use 'let's' with an apostrophe for 'let us'."
                })

        # 2.3. Subject-verb agreement: "I lets" → "I let"
        if " i lets " in text_lower or text_lower.startswith("i lets "):
            idx = text_lower.find("i lets")
            detected_errors.append({
                "type": "agreement",
                "category": "grammar",
                "original": "I lets",
                "correction": "I let",
                "span": {"start": idx, "end": idx + 6},
                "explanation": "The verb form should be 'let' after 'I'."
            })

        # 2.4. Verb tense (for past context)
        if any(w in text_lower for w in ["yesterday", "last", "ago"]):
            for verb_base, verb_past in self.IRREGULAR_VERBS.items():
                if f" {verb_base} " in f" {text_lower} ":
                    idx = text_lower.find(verb_base)
                    detected_errors.append({
                        "type": "verb_tense",
                        "category": "grammar",
                        "original": verb_base,
                        "correction": verb_past,
                        "span": {"start": idx, "end": idx + len(verb_base)},
                        "explanation": f"Use past tense '{verb_past}' for past events."
                    })
                    break

        # 2.5. Greeting punctuation/comma: "hi" → "Hi,"
        if intent == "greeting":
            # Check if greeting needs comma after first word
            first_word = text_lower.split()[0] if text_lower else ""
            if first_word in ["hi", "hello", "hey"]:
                if "," not in text_original[:10]:  # Check first 10 chars for comma
                    detected_errors.append({
                        "type": "greeting_format",
                        "category": "style",
                        "original": first_word,
                        "correction": first_word.capitalize() + ",",
                        "span": {"start": 0, "end": len(first_word)},
                        "explanation": "Greetings are usually followed by a comma."
                    })

            # Check if greeting contains a question without ?
            if any(q in text_lower for q in ["how are you", "how's it going", "what's up"]):
                if not text_original.endswith("?"):
                    detected_errors.append({
                        "type": "punctuation",
                        "category": "style",
                        "original": text_original,
                        "correction": text_original + "?",
                        "span": {},
                        "explanation": "Questions should end with a question mark."
                    })

        # ============================================================================
        # 3. Generate Rewrite (minimal correction of original text)
        # ============================================================================
        rewrite = text_original  # Start with original

        # Apply corrections in reverse order (to maintain index positions)
        for error in reversed(detected_errors):
            if error["type"] == "contraction":
                rewrite = rewrite.replace("lets", "let's")
            elif error["type"] == "agreement":
                rewrite = rewrite.replace("I lets", "I let")
            elif error["type"] == "verb_tense":
                rewrite = rewrite.replace(error["original"], error["correction"])
            elif error["type"] == "punctuation":
                if not rewrite.endswith("?"):
                    rewrite = rewrite + "?"
            elif error["type"] == "greeting_format":
                # Capitalize first letter and add comma
                words = rewrite.split()
                if words:
                    words[0] = words[0].capitalize()
                    if not words[0].endswith(","):
                        words[0] = words[0] + ","
                    rewrite = " ".join(words)

        # Ensure rewrite is capitalized and ends with proper punctuation
        if rewrite and not rewrite[0].isupper():
            rewrite = rewrite[0].capitalize() + rewrite[1:]
        if rewrite and not rewrite.endswith((".", "?", "!")):
            # Add period only if it's not a question
            if intent != "question" or "?" not in rewrite:
                rewrite = rewrite + "."

        # Fallback if rewrite is too short (e.g., just "hi")
        if len(rewrite) < 5:
            rewrite = text_original + "."

        # ============================================================================
        # 4. Extract keywords (for topic/follow-up)
        # ============================================================================
        words = [w.strip(".,?!") for w in text_lower.split()]
        keywords = [w for w in words if w not in self.STOPWORDS and len(w) >= 4][:3]

        # ============================================================================
        # 5. Infer topic (for follow-up questions)
        # ============================================================================
        if any(w in text_lower for w in ["yesterday", "last", "ago"]):
            topic = "past_simple"
        elif any(w in text_lower for w in ["tomorrow", "next", "will"]):
            topic = "future"
        elif any(w in text_lower for w in ["now", "currently"]) or text_lower.strip().endswith("ing"):
            topic = "present_continuous"
        elif any(w in text_lower for w in ["like", "enjoy", "love", "hobbies", "free time"]):
            topic = "hobbies"
        elif any(w in text_lower for w in ["work", "job", "office", "company"]):
            topic = "work"
        elif intent == "greeting":
            topic = "getting_started"
        else:
            topic = lesson_frame.get("topic", "general")

        # ============================================================================
        # 6. Generate follow-up question
        # ============================================================================
        follow_ups_by_topic = {
            "past_simple": ["What did you do next?", "Tell me more about it.", "How was it?"],
            "future": ["What are your plans?", "Who will go with you?", "What do you need?"],
            "present_continuous": ["How long have you been doing that?", "How is it going?"],
            "getting_started": ["How are you today?", "What would you like to practice?", "Ready to start?"],
            "general": ["Can you tell me more?", "What else?", "How does that sound?"]
        }

        topic_follow_ups = follow_ups_by_topic.get(topic, follow_ups_by_topic["general"])
        # Use deterministic selection (sum of ord instead of hash for stability)
        seed = sum(ord(c) for c in text_lower) % len(topic_follow_ups)
        follow_up = topic_follow_ups[seed]

        # ============================================================================
        # 7. Generate correction text (one-sentence explanation)
        # ============================================================================
        if detected_errors:
            first_error = detected_errors[0]
            correction_text = first_error["explanation"]
        else:
            if intent == "greeting":
                correction_text = "Great to hear from you!"
            elif intent == "question":
                correction_text = "Good question!"
            else:
                correction_text = "Your sentence looks good."

        return {
            "keywords": keywords,
            "intent": intent,
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
            # Use canonical category from analysis (grammar, style, etc)
            # NOT the error type (contraction, punctuation, etc.)
            category = error.get("category", "grammar")

            issue = {
                "category": category,
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
