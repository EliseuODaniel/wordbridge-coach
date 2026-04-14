"""Text-analysis helpers for the mock LLM provider."""

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


def _analyze_text(text: str, lesson_frame: dict) -> dict:
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

    # Greeting patterns (English, Portuguese, Spanish)
    greetings = [
        "hi", "hello", "hey",
        "good morning", "good afternoon", "good evening",
        "ola", "olá", "oi", "bom dia", "boa tarde", "boa noite",  # PT
        "hola", "buen día", "buenas tardes", "buenas noches"  # ES
    ]
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

    # 2.2b. Common contractions: im, dont, cant, wont, etc.
    contractions_map = {
        "im": "I'm",
        "dont": "don't",
        "doesnt": "doesn't",
        "wont": "won't",
        "cant": "can't",
        "couldnt": "couldn't",
        "shouldnt": "shouldn't",
        "wouldnt": "wouldn't",
    }

    # Check each contraction pattern (as whole word, not substring)
    for wrong, correct in contractions_map.items():
        # Match whole word only (surrounded by spaces or at start/end)
        pattern_start = f" {wrong} "
        pattern_start_sentence = f"{wrong} "  # At start
        pattern_end = f" {wrong}"  # At end

        if pattern_start in text_lower or pattern_start_sentence in text_lower or pattern_end in text_lower:
            # Find the index
            idx = text_lower.find(wrong)
            detected_errors.append({
                "type": "contraction",
                "category": "grammar",
                "original": wrong,
                "correction": correct,
                "span": {"start": idx, "end": idx + len(wrong)},
                "explanation": f"Use '{correct}' with an apostrophe."
            })

    # 2.2c. Lowercase "i" (standalone, not part of another word)
    # Check for " i " (surrounded by spaces) or at start/end of sentence
    words = text_lower.split()
    for i, word in enumerate(words):
        if word == "i" and word not in STOPWORDS:
            # This is a standalone lowercase "i"
            # Find its position in original text
            idx = text_lower.find(" i ")
            if idx == -1:
                # Check at start
                if text_lower.startswith("i "):
                    idx = 0
                # Check at end
                elif text_lower.endswith(" i"):
                    idx = text_lower.rfind(" i")

            if idx >= 0:
                detected_errors.append({
                    "type": "capitalization",
                    "category": "grammar",
                    "original": "i",
                    "correction": "I",
                    "span": {"start": idx, "end": idx + 1},
                    "explanation": "The pronoun 'I' must always be capitalized."
                })
                break  # Only report first occurrence

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
        for verb_base, verb_past in IRREGULAR_VERBS.items():
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
            # Handle all contractions (lets, im, dont, cant, wont, etc.)
            wrong = error["original"]
            correct = error["correction"]
            # Replace whole-word matches only (case-insensitive)
            import re
            pattern = r'\b' + re.escape(wrong) + r'\b'
            rewrite = re.sub(pattern, correct, rewrite, flags=re.IGNORECASE)
        elif error["type"] == "capitalization":
            # Handle i → I
            rewrite = rewrite.replace(" i ", " I ")
            if rewrite.startswith("i "):
                rewrite = "I " + rewrite[2:]
            if rewrite.endswith(" i"):
                rewrite = rewrite[:-2] + " I"
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

    # Ensure rewrite is capitalized
    if rewrite and not rewrite[0].isupper():
        rewrite = rewrite[0].capitalize() + rewrite[1:]

    if len(rewrite) < 5:
        rewrite = text_original

    if rewrite and not rewrite.endswith((".", "?", "!")):
        should_be_question = intent == "question" or (
            intent == "greeting" and any(q in text_lower for q in ["how are you", "how's it going", "what's up"])
        )
        rewrite = rewrite + ("?" if should_be_question else ".")

    # ============================================================================
    # 4. Extract keywords (for topic/follow-up)
    # ============================================================================
    words = [w.strip(".,?!") for w in text_lower.split()]
    keywords = [w for w in words if w not in STOPWORDS and len(w) >= 4][:3]

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
