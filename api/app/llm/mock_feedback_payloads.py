"""Feedback payload helpers for the mock LLM provider."""

import random
from typing import Any, Dict

from app.llm.mock_text_analysis import _analyze_text


async def micro_eval(
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
    analysis = _analyze_text(draft, lesson_frame)

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
        "micro_tip": micro_tip,
        # Rich signals for analysis panel
        "topic": analysis.get("topic"),
        "intent": analysis.get("intent"),
        "rewrite": analysis.get("rewrite")
    }


async def autocomplete(
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
    analysis = _analyze_text(draft, lesson_frame)
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


async def generate_teacher_analysis(
    user_message: str,
    context: str,
    lesson_frame: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate teacher analysis as JSON (separate from chat reply).

    Returns structured analysis with:
    - rewrite: Corrected version of user's message
    - corrections: List of {mistake, fix, why}
    - teacher_summary: Brief pedagogical feedback
    - next_practice: 2-3 suggested practice sentences
    """
    # Analyze user message to detect common errors
    analysis = _analyze_text(user_message, lesson_frame)
    topic = analysis["topic"]

    # Detect common errors and generate corrections
    corrections = []
    rewrite = user_message

    # Check for common mistakes
    if "enjoyed to" in user_message.lower():
        corrections.append({
            "mistake": "enjoyed to sleep",
            "fix": "enjoyed sleeping",
            "why": "After 'enjoy', use the gerund (-ing form) not infinitive (to + verb)"
        })
        rewrite = user_message.replace("enjoyed to", "enjoyed ")

    elif "went to" in user_message.lower() and "go" in user_message.lower():
        corrections.append({
            "mistake": "go to",
            "fix": "went to",
            "why": "Use past simple 'went' for past actions, not base form 'go'"
        })
        rewrite = user_message.replace("go to", "went to")

    elif "i like" in user_message.lower():
        corrections.append({
            "mistake": user_message,
            "fix": user_message,
            "why": "Good sentence structure! 'I like' is correctly followed by the gerund."
        })

    # Generate teacher summary based on topic
    teacher_summaries = {
        "past_simple": "Good practice with past tense! Remember to use irregular verb forms correctly.",
        "future": "Nice work on future forms! Keep practicing 'will' and 'going to' patterns.",
        "present_continuous": "Great use of present continuous for actions happening now!",
        "hobbies": "Excellent vocabulary for talking about interests and activities!",
        "work": "Professional language is developing well! Keep expanding work-related vocabulary.",
        "weekend_plans": "Good use of future time expressions! Your planning vocabulary is clear.",
        "getting_started": "Great beginning! Focus on basic sentence structure and word order.",
        "default": "Good effort! Keep practicing to build confidence and fluency."
    }

    teacher_summary = teacher_summaries.get(topic, teacher_summaries["default"])

    # Generate next practice sentences based on topic
    practice_sentences_map = {
        "past_simple": [
            "I _____ (go) to the cinema yesterday.",
            "She _____ (eat) pizza last night.",
            "We _____ (see) a beautiful sunset."
        ],
        "future": [
            "Tomorrow I _____ (visit) my grandmother.",
            "Next week we _____ (travel) to the beach.",
            "I _____ (study) English tonight."
        ],
        "present_continuous": [
            "Now I _____ (read) a book.",
            "She _____ (work) on her project.",
            "They _____ (play) football in the park."
        ],
        "hobbies": [
            "I enjoy _____ (paint) in my free time.",
            "My hobby is _____ (play) the guitar.",
            "I love _____ (cook) Italian food."
        ],
        "default": [
            "Practice makes perfect!",
            "Keep up the good work!",
            "Try another example."
        ]
    }

    next_practice = practice_sentences_map.get(topic, practice_sentences_map["default"])

    return {
        "rewrite": rewrite,
        "corrections": corrections,
        "teacher_summary": teacher_summary,
        "next_practice": next_practice[:3]  # Max 3 practice sentences
    }
