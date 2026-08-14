"""Pedagogical profile and memory helpers for Chat Coach."""

from __future__ import annotations

from collections import Counter
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.time import utc_now, utc_today
from app.models import (
    ChatConversation,
    ChatLessonHistory,
    ChatMessage,
    ReviewEvent,
    User,
    UserCardState,
    UserSessionStats,
)
from app.models.user_card_state import MemoryStage

MAX_PROFILE_ITEMS = 3
RECENT_ANALYSIS_LIMIT = 8
DEFAULT_CONVERSATION_TOPIC = "getting_started"

LANGUAGE_NAMES = {
    "en": "English",
    "pt": "Portuguese",
    "es": "Spanish",
    "fr": "French",
}

GOAL_TO_TOPIC = {
    "past_time_reference": "travel",
    "article_choice": "daily_routines",
    "preposition_choice": "city_navigation",
    "question_formation": "weekend_plans",
    "sentence_order": "introductions",
    "vocabulary_precision": "food_and_preferences",
    "conversation_confidence": DEFAULT_CONVERSATION_TOPIC,
    "response_expansion": "daily_life",
    "fluency_expansion": "opinions_and_explanations",
}


def _language_name(language_code: str | None) -> str:
    code = (language_code or "en").lower()
    return LANGUAGE_NAMES.get(code, code)


def _resolve_feedback_language_code(user: User | None) -> str:
    if user and getattr(user, "language_preference", None):
        return str(user.language_preference).lower()

    native_language = getattr(user, "native_language_obj", None)
    if native_language and getattr(native_language, "code", None):
        return str(native_language.code).lower()

    return "en"


def _resolve_target_language_code(user: User | None) -> str:
    target_language = getattr(user, "target_language_obj", None)
    if target_language and getattr(target_language, "code", None):
        return str(target_language.code).lower()

    return "en"


def _normalize_accuracy(accuracy_last_20: float | None) -> float | None:
    if accuracy_last_20 is None:
        return None
    return round(max(0.0, min(1.0, float(accuracy_last_20))), 2)


def _normalize_ratio(value: float | None) -> float | None:
    if value is None:
        return None
    return round(max(0.0, min(1.0, float(value))), 2)


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _classify_review_pressure(*, due_review_count: int, relearn_queue_count: int, daily_new_limit: int) -> str:
    load_factor = _safe_ratio(due_review_count + (relearn_queue_count * 1.5), max(daily_new_limit, 1))
    if due_review_count >= 30 or relearn_queue_count >= 6 or load_factor >= 3.0:
        return "high"
    if due_review_count >= 10 or relearn_queue_count >= 2 or load_factor >= 1.2:
        return "medium"
    return "low"


def _classify_retention_band(retention_score: float | None) -> str:
    if retention_score is None:
        return "unknown"
    if retention_score < 0.6:
        return "fragile"
    if retention_score < 0.82:
        return "building"
    return "stable"


def derive_pedagogical_metrics(
    *,
    daily_new_limit: int,
    accuracy_last_20: float | None,
    average_retention: float | None,
    due_review_count: int,
    relearn_queue_count: int,
    difficult_card_count: int,
    mature_ratio: float | None,
    hint_ratio: float | None,
    average_attempts: float | None,
    cards_seen_today: int,
    session_new_ratio: float | None,
    preferred_mode: str,
) -> dict[str, Any]:
    """Convert raw study signals into compact pedagogical metrics."""
    accuracy = _normalize_accuracy(accuracy_last_20)
    retention_score = _normalize_ratio(
        _average(
            [
                metric
                for metric in (average_retention, accuracy)
                if metric is not None
            ]
        )
    )
    review_pressure = _classify_review_pressure(
        due_review_count=due_review_count,
        relearn_queue_count=relearn_queue_count,
        daily_new_limit=daily_new_limit,
    )
    hint_ratio = _normalize_ratio(hint_ratio) or 0.0
    average_attempts = round(max(1.0, float(average_attempts or 1.0)), 1)
    mature_ratio = _normalize_ratio(mature_ratio) or 0.0
    session_new_ratio = _normalize_ratio(session_new_ratio) or 0.0

    support_load = 0
    if accuracy is None or accuracy < 0.6:
        support_load += 2
    elif accuracy < 0.75:
        support_load += 1
    if retention_score is not None and retention_score < 0.6:
        support_load += 1
    if hint_ratio >= 0.45:
        support_load += 1
    if average_attempts >= 1.8:
        support_load += 1
    if difficult_card_count >= 5:
        support_load += 1
    if review_pressure == "high":
        support_load += 1

    stretch_capacity = 0
    if accuracy is not None and accuracy >= 0.88:
        stretch_capacity += 1
    if retention_score is not None and retention_score >= 0.82:
        stretch_capacity += 1
    if hint_ratio <= 0.15:
        stretch_capacity += 1
    if average_attempts <= 1.1:
        stretch_capacity += 1
    if difficult_card_count <= 1:
        stretch_capacity += 1
    if review_pressure != "high":
        stretch_capacity += 1

    has_retention_signal = retention_score is not None

    if support_load >= 3:
        difficulty_signal = "support_needed"
    elif has_retention_signal and stretch_capacity >= 4:
        difficulty_signal = "ready_to_push"
    else:
        difficulty_signal = "on_target"

    if review_pressure == "high" or difficulty_signal == "support_needed":
        recommended_pace = "stabilize"
    elif difficulty_signal == "ready_to_push":
        recommended_pace = "accelerate"
    else:
        recommended_pace = "balance"

    if difficulty_signal == "support_needed":
        recommended_mode = "lingvist"
    elif review_pressure == "high":
        recommended_mode = "spec4"
    elif difficulty_signal == "ready_to_push":
        recommended_mode = "chat"
    else:
        recommended_mode = preferred_mode or "spec4"

    if difficulty_signal == "support_needed":
        cefr_readiness = "solidify_current_band"
    elif difficulty_signal == "ready_to_push":
        cefr_readiness = "ready_to_probe_next_band"
    else:
        cefr_readiness = "operating_at_band"

    return {
        "recent_accuracy": accuracy,
        "retention_score": retention_score,
        "retention_band": _classify_retention_band(retention_score),
        "review_pressure": review_pressure,
        "due_review_count": int(due_review_count),
        "relearn_queue_count": int(relearn_queue_count),
        "difficult_card_count": int(difficult_card_count),
        "mature_ratio": mature_ratio,
        "recent_hint_ratio": hint_ratio,
        "average_attempts": average_attempts,
        "cards_seen_today": int(cards_seen_today),
        "session_new_ratio": session_new_ratio,
        "recommended_pace": recommended_pace,
        "recommended_mode": recommended_mode,
        "difficulty_signal": difficulty_signal,
        "cefr_readiness": cefr_readiness,
    }


def collect_pedagogical_metrics(
    db: Session,
    user_id: str,
    *,
    user: User | None = None,
) -> dict[str, Any]:
    """Collect study signals that calibrate cross-mode pedagogy."""
    current_user = user or db.query(User).filter(User.id == user_id).first()
    daily_new_limit = int(getattr(current_user, "daily_new_limit", 10) or 10)
    preferred_mode = str(getattr(current_user, "mode", "spec4") or "spec4")
    accuracy_last_20 = _normalize_accuracy(getattr(current_user, "accuracy_last_20", None))

    card_states = (
        db.query(UserCardState)
        .filter(UserCardState.user_id == user_id)
        .all()
    )
    reviewed_states = [state for state in card_states if int(getattr(state, "total_reviews", 0) or 0) > 0]
    mature_count = sum(1 for state in reviewed_states if state.status == MemoryStage.MATURE)
    average_retention = _average(
        [
            _safe_ratio(int(state.correct_reviews or 0), int(state.total_reviews or 0))
            for state in reviewed_states
            if int(state.total_reviews or 0) > 0
        ]
    )
    difficult_card_count = sum(
        1
        for state in reviewed_states
        if int(state.total_reviews or 0) >= 3
        and _safe_ratio(int(state.correct_reviews or 0), int(state.total_reviews or 0)) < 0.6
    )
    mature_ratio = _safe_ratio(mature_count, len(reviewed_states)) if reviewed_states else None

    due_review_count = (
        db.query(UserCardState)
        .filter(
            UserCardState.user_id == user_id,
            UserCardState.next_review_at <= utc_now(),
            UserCardState.status.in_([MemoryStage.LEARNING, MemoryStage.REVIEW, MemoryStage.MATURE]),
        )
        .count()
    )
    relearn_queue_count = (
        db.query(UserCardState)
        .filter(
            UserCardState.user_id == user_id,
            UserCardState.is_relearn == True,
        )
        .count()
    )

    recent_reviews = (
        db.query(ReviewEvent)
        .filter(ReviewEvent.user_id == user_id)
        .order_by(desc(ReviewEvent.created_at))
        .limit(12)
        .all()
    )
    hint_events = 0
    attempt_values: list[float] = []
    for review in recent_reviews:
        lingvist_hints = review.hints_used_lingvist if isinstance(review.hints_used_lingvist, dict) else {}
        if int(review.hints_used or 0) > 0 or any(bool(value) for value in lingvist_hints.values()):
            hint_events += 1
        attempt_values.append(float(max(int(review.attempts or 1), int(review.attempt_index or 1))))

    hint_ratio = _safe_ratio(hint_events, len(recent_reviews)) if recent_reviews else None
    average_attempts = _average(attempt_values)

    today_stats = (
        db.query(UserSessionStats)
        .filter(
            UserSessionStats.user_id == user_id,
            UserSessionStats.date == utc_today(),
        )
        .first()
    )
    cards_seen_today = int(getattr(today_stats, "cards_shown", 0) or 0)
    session_new_ratio = None
    if today_stats and int(today_stats.cards_shown or 0) > 0:
        session_new_ratio = _safe_ratio(
            int(today_stats.new_cards_shown or 0),
            int(today_stats.cards_shown or 0),
        )

    return derive_pedagogical_metrics(
        daily_new_limit=daily_new_limit,
        accuracy_last_20=accuracy_last_20,
        average_retention=average_retention,
        due_review_count=due_review_count,
        relearn_queue_count=relearn_queue_count,
        difficult_card_count=difficult_card_count,
        mature_ratio=mature_ratio,
        hint_ratio=hint_ratio,
        average_attempts=average_attempts,
        cards_seen_today=cards_seen_today,
        session_new_ratio=session_new_ratio,
        preferred_mode=preferred_mode,
    )


def _contains_any(text: str, candidates: tuple[str, ...]) -> bool:
    lowered = text.casefold()
    return any(candidate in lowered for candidate in candidates)


def estimate_cefr_level(word_goal_rank: int, accuracy_last_20: float | None) -> str:
    """Return a safe instructional default, never a vocabulary-derived claim.

    This function stays temporarily for call-site compatibility while
    multi-skill observations become the source of proficiency evidence.
    """
    return "A2"


def determine_scaffolding_level(
    accuracy_last_20: float | None,
    pedagogical_metrics: dict[str, Any] | None = None,
) -> str:
    """Map recent accuracy to a coarse scaffolding mode."""
    pedagogical_metrics = dict(pedagogical_metrics or {})
    difficulty_signal = str(pedagogical_metrics.get("difficulty_signal") or "")
    review_pressure = str(pedagogical_metrics.get("review_pressure") or "")
    hint_ratio = float(pedagogical_metrics.get("recent_hint_ratio") or 0.0)

    if difficulty_signal == "support_needed" or review_pressure == "high" or hint_ratio >= 0.45:
        return "high_support"
    if difficulty_signal == "ready_to_push" and review_pressure != "high" and hint_ratio <= 0.15:
        return "light_support"

    accuracy = _normalize_accuracy(accuracy_last_20)
    if accuracy is None or accuracy < 0.6:
        return "high_support"
    if accuracy < 0.85:
        return "guided_practice"
    return "light_support"


def determine_coaching_focus(mode: str, scaffolding_level: str) -> str:
    """Infer the coaching stance used in prompts."""
    if mode == "lingvist":
        if scaffolding_level == "high_support":
            return "controlled_input_and_high_frequency_sentences"
        if scaffolding_level == "guided_practice":
            return "frequency_progression_with_targeted_sentence_building"
        return "high_frequency_fluency_expansion"

    if scaffolding_level == "high_support":
        return "sentence_patterns_and_confidence_building"
    if scaffolding_level == "guided_practice":
        return "guided_self_correction_and_topic_expansion"
    return "fluency_expansion_and_precision"


def determine_lesson_stage(scaffolding_level: str) -> str:
    """Map scaffolding to an explicit pedagogical stage."""
    if scaffolding_level == "high_support":
        return "stabilize_foundations"
    if scaffolding_level == "guided_practice":
        return "guided_expansion"
    return "fluency_push"


def determine_support_strategy(scaffolding_level: str) -> str:
    """Explain how the tutor should intervene at the current stage."""
    if scaffolding_level == "high_support":
        return "Ask for one short sentence, then guide self-correction before expanding."
    if scaffolding_level == "guided_practice":
        return "Prompt a clearer retry plus one extra detail after the learner self-corrects."
    return "Use lighter nudges and push for more precise, natural follow-up turns."


def infer_primary_focus(student_profile: dict[str, Any]) -> str:
    """Pick the most useful current focus label for adaptive planning."""
    for group in (
        student_profile.get("weaknesses", []),
        student_profile.get("common_errors", []),
        student_profile.get("strengths", []),
    ):
        for item in group or []:
            value = str(item or "").strip()
            if value:
                return value

    coaching_focus = str(student_profile.get("coaching_focus") or "").strip()
    if coaching_focus:
        return coaching_focus.replace("_", " ")

    pedagogical_metrics = dict(student_profile.get("pedagogical_metrics") or {})
    if pedagogical_metrics.get("review_pressure") == "high":
        return "consolidate overdue review patterns before adding novelty"
    if pedagogical_metrics.get("difficulty_signal") == "support_needed":
        return "build one accurate sentence before expanding"
    if pedagogical_metrics.get("difficulty_signal") == "ready_to_push":
        return "expand with a second detail and more precise vocabulary"

    return "build confidence with clear sentences"


def infer_learning_goal(
    primary_focus: str,
    scaffolding_level: str,
    pedagogical_metrics: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Turn the current focus into a stable goal key plus a prompt-friendly goal label."""
    focus = primary_focus.casefold()
    pedagogical_metrics = dict(pedagogical_metrics or {})
    recommended_pace = str(pedagogical_metrics.get("recommended_pace") or "balance")

    if _contains_any(focus, ("past", "yesterday", "irregular verb", "went", "verb tense")):
        return (
            "past_time_reference",
            "stabilize past-time verbs in short personal sentences"
            if recommended_pace != "accelerate"
            else "use past-time verbs accurately while adding one extra detail",
        )
    if _contains_any(focus, ("article", "a/an", "the ")):
        return (
            "article_choice",
            "choose articles accurately when naming concrete people, places, and objects",
        )
    if _contains_any(focus, ("preposition", "in ", "on ", "at ", "to ", "from ")):
        return (
            "preposition_choice",
            "use location and movement prepositions more accurately",
        )
    if _contains_any(focus, ("question", "ask", "wh-", "auxiliary")):
        return (
            "question_formation",
            "build clearer questions and short answers",
        )
    if _contains_any(focus, ("order", "word order", "sentence order", "complete sentence")):
        return (
            "sentence_order",
            "keep sentence order natural and complete",
        )
    if _contains_any(focus, ("vocabulary", "word choice", "precision", "meaning")):
        return (
            "vocabulary_precision",
            "choose more precise high-frequency vocabulary",
        )

    if scaffolding_level == "high_support":
        return (
            "conversation_confidence",
            "build one clear high-frequency sentence before expanding the idea",
        )
    if scaffolding_level == "guided_practice":
        return (
            "response_expansion",
            "answer clearly and add one supporting detail"
            if recommended_pace != "stabilize"
            else "answer clearly with one accurate pattern before expanding",
        )
    return (
        "fluency_expansion",
        "sustain the topic with more precise and natural language"
        if recommended_pace != "stabilize"
        else "keep the topic moving without losing control of the target pattern",
    )


def infer_expected_intent(
    goal_key: str,
    scaffolding_level: str,
    pedagogical_metrics: dict[str, Any] | None = None,
) -> str:
    """Describe the next turn shape expected from the learner."""
    pedagogical_metrics = dict(pedagogical_metrics or {})
    if pedagogical_metrics.get("recommended_pace") == "stabilize" and goal_key in {
        "conversation_confidence",
        "response_expansion",
    }:
        return "produce_one_short_controlled_reply"

    if goal_key == "past_time_reference":
        return "describe_one_past_event_clearly"
    if goal_key == "article_choice":
        return "name_people_places_and_objects_with_correct_articles"
    if goal_key == "preposition_choice":
        return "describe_location_or_movement_with_correct_prepositions"
    if goal_key == "question_formation":
        return "ask_or_answer_one_clear_question"
    if goal_key == "sentence_order":
        return "build_one_complete_sentence_in_natural_order"
    if goal_key == "vocabulary_precision":
        return "replace_generic_words_with_more_precise_high_frequency_options"
    if scaffolding_level == "high_support":
        return "share_one_short_idea_confidently"
    if scaffolding_level == "guided_practice":
        return "answer_and_add_one_supporting_detail"
    return "sustain_the_topic_with_detail_and_follow_up"


def choose_recommended_topic(
    current_topic: str | None,
    recent_topics: list[str] | None,
    goal_key: str,
) -> str:
    """Prefer a proven topic when available, otherwise choose a pedagogically useful fallback."""
    topic = str(current_topic or "").strip()
    if topic and topic != DEFAULT_CONVERSATION_TOPIC:
        return topic

    for recent_topic in recent_topics or []:
        value = str(recent_topic or "").strip()
        if value:
            return value

    return GOAL_TO_TOPIC.get(goal_key, DEFAULT_CONVERSATION_TOPIC)


def build_success_criteria(
    scaffolding_level: str,
    primary_focus: str,
    pedagogical_metrics: dict[str, Any] | None = None,
) -> list[str]:
    """Create compact success criteria for the current pedagogical step."""
    pedagogical_metrics = dict(pedagogical_metrics or {})
    criteria = [f"Address the main focus: {primary_focus}"]

    if scaffolding_level == "high_support":
        criteria.extend(
            [
                "Keep the response to one clear sentence.",
                "Self-correct the most important form before adding detail.",
            ]
        )
    elif scaffolding_level == "guided_practice":
        criteria.extend(
            [
                "Add one supporting detail after the core answer.",
                "Use the corrected structure without overexplaining.",
            ]
        )
    else:
        criteria.extend(
            [
                "Keep the conversation moving with a natural follow-up.",
                "Improve precision without losing fluency.",
            ]
        )

    if pedagogical_metrics.get("review_pressure") == "high":
        criteria.append("Favor accurate retrieval over adding new complexity.")
    elif pedagogical_metrics.get("recommended_pace") == "accelerate":
        criteria.append("Add one natural follow-up detail once the core answer is correct.")

    return criteria[:MAX_PROFILE_ITEMS]


def build_explicit_pedagogical_state(
    student_profile: dict[str, Any],
    lesson_frame: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an explicit pedagogical state object used across modules."""
    lesson_frame = dict(lesson_frame or {})
    seed_state = dict(student_profile.get("pedagogical_state") or {})
    pedagogical_metrics = dict(student_profile.get("pedagogical_metrics") or {})
    scaffolding_level = str(student_profile.get("scaffolding_level", "guided_practice"))
    lesson_stage = determine_lesson_stage(scaffolding_level)
    primary_focus = infer_primary_focus(student_profile)
    if primary_focus == "build confidence with clear sentences" and seed_state.get("primary_focus"):
        primary_focus = str(seed_state["primary_focus"])
    if pedagogical_metrics.get("recommended_pace") == "stabilize":
        lesson_stage = "stabilize_foundations"
    elif pedagogical_metrics.get("recommended_pace") == "accelerate":
        lesson_stage = "fluency_push"
    goal_key, learning_goal = infer_learning_goal(
        primary_focus,
        scaffolding_level,
        pedagogical_metrics,
    )
    recommended_topic = choose_recommended_topic(
        current_topic=lesson_frame.get("topic"),
        recent_topics=student_profile.get("recent_topics", []),
        goal_key=goal_key,
    )

    return {
        "lesson_stage": lesson_stage,
        "primary_focus": primary_focus,
        "goal_key": goal_key,
        "session_goal": learning_goal,
        "expected_intent": infer_expected_intent(
            goal_key,
            scaffolding_level,
            pedagogical_metrics,
        ),
        "recommended_topic": recommended_topic,
        "support_strategy": determine_support_strategy(scaffolding_level),
        "difficulty_signal": pedagogical_metrics.get("difficulty_signal", "on_target"),
        "review_pressure": pedagogical_metrics.get("review_pressure", "medium"),
        "recommended_pace": pedagogical_metrics.get("recommended_pace", "balance"),
        "recommended_mode": pedagogical_metrics.get("recommended_mode", student_profile.get("mode", "spec4")),
        "retention_band": pedagogical_metrics.get("retention_band", "unknown"),
    }


def merge_ranked_strings(*groups: list[str], limit: int = MAX_PROFILE_ITEMS) -> list[str]:
    """Merge ordered string lists while keeping only the first unique non-empty values."""
    merged: list[str] = []
    seen: set[str] = set()

    for group in groups:
        for item in group or []:
            value = str(item or "").strip()
            if not value:
                continue
            key = value.casefold()
            if key in seen:
                continue
            merged.append(value)
            seen.add(key)
            if len(merged) >= limit:
                return merged

    return merged


def extract_recent_chat_signals(db: Session, user_id: str, limit: int = RECENT_ANALYSIS_LIMIT) -> dict[str, list[str]]:
    """Collect recent teacher-analysis signals across the user's past conversations."""
    recent_user_messages = (
        db.query(ChatMessage)
        .join(ChatConversation, ChatMessage.conversation_id == ChatConversation.id)
        .filter(
            ChatConversation.user_id == user_id,
            ChatMessage.role == "user",
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )

    strengths_counter: Counter[str] = Counter()
    focus_counter: Counter[str] = Counter()
    errors_counter: Counter[str] = Counter()
    topics_counter: Counter[str] = Counter()

    for message in recent_user_messages:
        metadata = message.metadata_json or {}
        analysis = metadata.get("teacher_analysis")
        if not isinstance(analysis, dict):
            continue

        for strength in analysis.get("strengths", []) or []:
            value = str(strength or "").strip()
            if value:
                strengths_counter[value] += 1

        for focus_area in analysis.get("focus_areas", []) or []:
            value = str(focus_area or "").strip()
            if value:
                focus_counter[value] += 1

        for correction in analysis.get("corrections", []) or []:
            if not isinstance(correction, dict):
                continue
            value = str(correction.get("mistake") or correction.get("fix") or "").strip()
            if value:
                errors_counter[value] += 1

        lesson_frame = getattr(getattr(message, "conversation", None), "lesson_frame_json", {}) or {}
        topic = str(lesson_frame.get("topic") or "").strip()
        if topic:
            topics_counter[topic] += 1

    return {
        "strengths": [item for item, _ in strengths_counter.most_common(MAX_PROFILE_ITEMS)],
        "focus_areas": [item for item, _ in focus_counter.most_common(MAX_PROFILE_ITEMS)],
        "common_errors": [item for item, _ in errors_counter.most_common(MAX_PROFILE_ITEMS)],
        "topics": [item for item, _ in topics_counter.most_common(MAX_PROFILE_ITEMS)],
    }


def build_student_profile(
    user: User | None,
    *,
    recent_signals: dict[str, list[str]] | None = None,
    seed_profile: dict[str, Any] | None = None,
    pedagogical_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the persisted pedagogical profile used by Chat Coach."""
    recent_signals = recent_signals or {}
    seed_profile = dict(seed_profile or {})
    pedagogical_metrics = dict(
        pedagogical_metrics
        or seed_profile.get("pedagogical_metrics", {})
        or {}
    )

    word_goal_rank = int(getattr(user, "word_goal_rank", seed_profile.get("word_goal_rank", 1000)))
    accuracy_last_20 = _normalize_accuracy(
        getattr(user, "accuracy_last_20", seed_profile.get("accuracy_last_20"))
    )
    scaffolding_level = determine_scaffolding_level(accuracy_last_20, pedagogical_metrics)
    mode = str(getattr(user, "mode", seed_profile.get("mode", "spec4")))
    resolved_scaffolding_level = scaffolding_level if pedagogical_metrics else seed_profile.get(
        "scaffolding_level",
        scaffolding_level,
    )
    feedback_language_code = _resolve_feedback_language_code(user)
    target_language_code = _resolve_target_language_code(user)

    strengths = merge_ranked_strings(
        seed_profile.get("strengths", []),
        recent_signals.get("strengths", []),
    )
    weaknesses = merge_ranked_strings(
        seed_profile.get("weaknesses", []),
        recent_signals.get("focus_areas", []),
    )
    common_errors = merge_ranked_strings(
        seed_profile.get("common_errors", []),
        recent_signals.get("common_errors", []),
        recent_signals.get("focus_areas", []),
    )
    recent_topics = merge_ranked_strings(
        seed_profile.get("recent_topics", []),
        recent_signals.get("topics", []),
    )

    return {
        "cefr_level": seed_profile.get(
            "cefr_level",
            estimate_cefr_level(word_goal_rank, accuracy_last_20),
        ),
        "proficiency_basis": (
            seed_profile.get("proficiency_basis")
            or ("persisted_instructional_band" if seed_profile.get("cefr_level") else "unassessed_instructional_default")
        ),
        "cefr_certified": False,
        "common_errors": common_errors,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "feedback_language": _language_name(feedback_language_code),
        "feedback_language_code": feedback_language_code,
        "target_language": _language_name(target_language_code),
        "target_language_code": target_language_code,
        "word_goal_rank": word_goal_rank,
        "accuracy_last_20": accuracy_last_20,
        "scaffolding_level": resolved_scaffolding_level,
        "coaching_focus": determine_coaching_focus(mode, resolved_scaffolding_level),
        "mode": mode,
        "recent_topics": recent_topics,
        "last_reflection_question": seed_profile.get("last_reflection_question"),
        "last_teacher_summary": seed_profile.get("last_teacher_summary"),
        "last_next_practice": merge_ranked_strings(seed_profile.get("last_next_practice", [])),
        "pedagogical_metrics": pedagogical_metrics,
        "pedagogical_state": dict(seed_profile.get("pedagogical_state", {})),
    }


def build_lesson_frame_diagnostics(
    student_profile: dict[str, Any],
    pedagogical_state: dict[str, Any],
) -> dict[str, Any]:
    """Project the most useful adaptation signals into the active lesson frame."""
    metrics = dict(student_profile.get("pedagogical_metrics") or {})
    return {
        "retention_band": metrics.get("retention_band", "unknown"),
        "difficulty_signal": metrics.get("difficulty_signal", "on_target"),
        "review_pressure": metrics.get("review_pressure", "medium"),
        "recommended_pace": metrics.get("recommended_pace", "balance"),
        "recommended_mode": metrics.get("recommended_mode", student_profile.get("mode", "spec4")),
        "cefr_readiness": metrics.get("cefr_readiness", "operating_at_band"),
        "cards_seen_today": metrics.get("cards_seen_today", 0),
        "due_review_count": metrics.get("due_review_count", 0),
        "difficult_card_count": metrics.get("difficult_card_count", 0),
        "retention_score": metrics.get("retention_score"),
        "focus_origin": (
            "recent_teacher_analysis"
            if student_profile.get("weaknesses") or student_profile.get("common_errors")
            else "study_metrics"
        ),
        "lesson_stage": pedagogical_state.get("lesson_stage", "guided_expansion"),
    }


def sync_student_profile_and_lesson_frame(
    student_profile: dict[str, Any],
    lesson_frame: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Keep the explicit pedagogical state synchronized across profile and lesson frame."""
    updated_profile = dict(student_profile or {})
    updated_lesson_frame = build_personalized_lesson_frame(lesson_frame, updated_profile)
    updated_profile["pedagogical_state"] = dict(
        updated_lesson_frame.get("pedagogical_profile", {}).get("pedagogical_state", {})
    )
    updated_profile["current_learning_goal"] = updated_lesson_frame.get("learning_goal")
    return updated_profile, updated_lesson_frame


def build_personalized_lesson_frame(lesson_frame: dict[str, Any], student_profile: dict[str, Any]) -> dict[str, Any]:
    """Attach pedagogical profile metadata to the lesson frame."""
    payload = dict(lesson_frame or {})
    pedagogical_state = build_explicit_pedagogical_state(student_profile, payload)
    scaffolding_level = student_profile.get("scaffolding_level", "guided_practice")
    pedagogical_metrics = dict(student_profile.get("pedagogical_metrics") or {})

    payload.setdefault("cefr_target", student_profile.get("cefr_level", "A2"))
    payload["topic"] = pedagogical_state["recommended_topic"]
    payload["learning_goal"] = pedagogical_state["session_goal"]
    payload["expected_intent"] = pedagogical_state["expected_intent"]
    payload["lesson_stage"] = pedagogical_state["lesson_stage"]
    payload["primary_focus"] = pedagogical_state["primary_focus"]
    payload["success_criteria"] = build_success_criteria(
        scaffolding_level,
        pedagogical_state["primary_focus"],
        pedagogical_metrics,
    )
    payload["diagnostics"] = build_lesson_frame_diagnostics(student_profile, pedagogical_state)
    payload["pedagogical_profile"] = {
        "feedback_language": student_profile.get("feedback_language", "English"),
        "scaffolding_level": scaffolding_level,
        "coaching_focus": student_profile.get("coaching_focus", "guided_self_correction_and_topic_expansion"),
        "recent_topics": student_profile.get("recent_topics", []),
        "pedagogical_metrics": pedagogical_metrics,
        "pedagogical_state": pedagogical_state,
    }
    return payload


def build_session_summary(student_profile: dict[str, Any]) -> str:
    """Render a compact longitudinal memory block for prompt context."""
    strengths = ", ".join(student_profile.get("strengths", [])) or "none recorded yet"
    focus = ", ".join(student_profile.get("weaknesses", [])) or "clear communication"
    topics = ", ".join(student_profile.get("recent_topics", [])) or "getting_started"
    accuracy = student_profile.get("accuracy_last_20")
    accuracy_label = f"{int(accuracy * 100)}%" if accuracy is not None else "unknown"
    pedagogical_state = student_profile.get("pedagogical_state", {}) or {}
    pedagogical_metrics = student_profile.get("pedagogical_metrics", {}) or {}
    active_focus = pedagogical_state.get("primary_focus", "clear communication")
    session_goal = pedagogical_state.get("session_goal", "Build momentum with short, clear replies")
    lesson_stage = pedagogical_state.get("lesson_stage", determine_lesson_stage(student_profile.get("scaffolding_level", "guided_practice")))

    return (
        "Longitudinal learner profile:\n"
        f"- Feedback language: {student_profile.get('feedback_language', 'English')}\n"
        f"- Target language: {student_profile.get('target_language', 'English')}\n"
        f"- Estimated CEFR: {student_profile.get('cefr_level', 'A2')}\n"
        f"- Scaffolding: {student_profile.get('scaffolding_level', 'guided_practice')}\n"
        f"- Lesson stage: {lesson_stage}\n"
        f"- Active focus: {active_focus}\n"
        f"- Session goal: {session_goal}\n"
        f"- Coaching focus: {student_profile.get('coaching_focus', 'guided_self_correction_and_topic_expansion')}\n"
        f"- Recent strengths: {strengths}\n"
        f"- Current focus areas: {focus}\n"
        f"- Recent topics: {topics}\n"
        f"- Vocabulary goal rank: {student_profile.get('word_goal_rank', 1000)}\n"
        f"- Accuracy last 20 cards: {accuracy_label}\n"
        f"- Retention signal: {pedagogical_metrics.get('retention_band', 'unknown')}\n"
        f"- Difficulty signal: {pedagogical_metrics.get('difficulty_signal', 'on_target')}\n"
        f"- Review pressure: {pedagogical_metrics.get('review_pressure', 'medium')}\n"
        f"- Recommended pace: {pedagogical_metrics.get('recommended_pace', 'balance')}\n"
        f"- CEFR readiness: {pedagogical_metrics.get('cefr_readiness', 'operating_at_band')}"
    )


def build_seed_chat_state(
    db: Session,
    user: User,
    *,
    base_lesson_frame: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Build the initial conversation state from user settings and recent history."""
    recent_signals = extract_recent_chat_signals(db, str(user.id))
    pedagogical_metrics = collect_pedagogical_metrics(db, str(user.id), user=user)
    student_profile = build_student_profile(
        user,
        recent_signals=recent_signals,
        pedagogical_metrics=pedagogical_metrics,
    )
    student_profile, lesson_frame = sync_student_profile_and_lesson_frame(
        student_profile,
        base_lesson_frame,
    )
    session_summary = build_session_summary(student_profile)
    return student_profile, lesson_frame, session_summary


def apply_teacher_analysis_to_profile(
    student_profile: dict[str, Any],
    teacher_analysis: dict[str, Any],
    lesson_frame: dict[str, Any],
) -> dict[str, Any]:
    """Update the profile with the latest strengths, focus areas, and topic."""
    payload = dict(student_profile or {})
    topic = str((lesson_frame or {}).get("topic") or "").strip()

    strength_updates = [str(item).strip() for item in teacher_analysis.get("strengths", []) or [] if str(item).strip()]
    focus_updates = [str(item).strip() for item in teacher_analysis.get("focus_areas", []) or [] if str(item).strip()]
    correction_updates = []
    for correction in teacher_analysis.get("corrections", []) or []:
        if not isinstance(correction, dict):
            continue
        value = str(correction.get("mistake") or correction.get("fix") or "").strip()
        if value:
            correction_updates.append(value)

    payload["strengths"] = merge_ranked_strings(strength_updates, payload.get("strengths", []))
    payload["weaknesses"] = merge_ranked_strings(focus_updates, payload.get("weaknesses", []))
    payload["common_errors"] = merge_ranked_strings(
        correction_updates,
        focus_updates,
        payload.get("common_errors", []),
    )
    payload["recent_topics"] = merge_ranked_strings(
        [topic] if topic else [],
        payload.get("recent_topics", []),
    )
    payload["last_reflection_question"] = teacher_analysis.get("reflection_question") or payload.get("last_reflection_question")
    payload["last_teacher_summary"] = teacher_analysis.get("teacher_summary") or payload.get("last_teacher_summary")
    payload["last_next_practice"] = merge_ranked_strings(
        teacher_analysis.get("next_practice", []),
        payload.get("last_next_practice", []),
    )
    return payload


def record_lesson_frame_snapshot(
    db: Session,
    conversation: ChatConversation,
    lesson_frame: dict[str, Any],
) -> None:
    """Persist a lesson-frame snapshot for longitudinal analytics."""
    db.add(
        ChatLessonHistory(
            conversation_id=conversation.id,
            lesson_frame_json=dict(lesson_frame or {}),
        )
    )


def build_learning_context(
    student_profile: dict[str, Any],
    lesson_frame: dict[str, Any],
    *,
    mode: str,
) -> dict[str, Any]:
    """Build a compact cross-mode learning context for card-based sessions."""
    pedagogical_state = dict(student_profile.get("pedagogical_state") or {})
    pedagogical_metrics = dict(student_profile.get("pedagogical_metrics") or {})
    if not pedagogical_state:
        _, synchronized_lesson_frame = sync_student_profile_and_lesson_frame(student_profile, lesson_frame)
        pedagogical_state = dict(
            synchronized_lesson_frame.get("pedagogical_profile", {}).get("pedagogical_state", {})
        )
        lesson_frame = synchronized_lesson_frame

    lesson_stage = pedagogical_state.get("lesson_stage", "guided_expansion")
    review_pressure = pedagogical_metrics.get("review_pressure", "medium")
    recommended_pace = pedagogical_metrics.get("recommended_pace", "balance")
    difficulty_signal = pedagogical_metrics.get("difficulty_signal", "on_target")

    if mode == "spec4":
        why_this_now = "Recognition practice to reinforce the current focus before freer production."
        if review_pressure == "high":
            why_this_now = "Fast recall practice to reduce overdue review pressure before new material."
        elif recommended_pace == "accelerate":
            why_this_now = "Use this fast review to confirm accuracy, then push into freer production."
    else:
        why_this_now = "High-frequency cloze practice to stabilize the target pattern before freer use."
        if difficulty_signal == "support_needed":
            why_this_now = "Short cloze practice to rebuild control with high-frequency sentences before freer chat."
        elif recommended_pace == "accelerate":
            why_this_now = "Use this cloze to keep fluency high while stretching vocabulary precision."
    if lesson_stage == "fluency_push":
        why_this_now = (
            "Use this fast review to sharpen precision while keeping fluency high."
            if mode == "spec4"
            else "Use this cloze to keep fluency high while pushing vocabulary precision."
        )

    return {
        "mode": mode,
        "cefr_level": student_profile.get("cefr_level", "A2"),
        "support_level": student_profile.get("scaffolding_level", "guided_practice"),
        "current_focus": pedagogical_state.get("primary_focus", infer_primary_focus(student_profile)),
        "session_goal": lesson_frame.get("learning_goal", pedagogical_state.get("session_goal", "practice conversation")),
        "topic": lesson_frame.get("topic", pedagogical_state.get("recommended_topic", DEFAULT_CONVERSATION_TOPIC)),
        "feedback_language": student_profile.get("feedback_language", "English"),
        "why_this_now": why_this_now,
        "retention_signal": pedagogical_metrics.get("retention_band"),
        "review_pressure": review_pressure,
        "difficulty_signal": difficulty_signal,
        "recommended_pace": recommended_pace,
        "next_mode_hint": pedagogical_metrics.get("recommended_mode"),
    }


def build_pedagogical_analytics_projection(
    student_profile: dict[str, Any],
    lesson_frame: dict[str, Any],
    *,
    mode: str,
    lesson_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Project the current pedagogical state into a compact analytics view.

    This keeps analytics read-side behavior explicit without introducing a new
    persistence table before the product has real longitudinal reporting needs.
    """
    history = [dict(item or {}) for item in (lesson_history or [])]
    context = build_learning_context(student_profile, lesson_frame, mode=mode)
    metrics = dict((student_profile or {}).get("pedagogical_metrics") or {})
    state = dict((student_profile or {}).get("pedagogical_state") or {})

    recent_focus_areas = merge_ranked_strings(
        [
            str(frame.get("primary_focus") or "").strip()
            for frame in history
            if str(frame.get("primary_focus") or "").strip()
        ],
        [str(context.get("current_focus") or "").strip()],
    )
    recent_stages = merge_ranked_strings(
        [
            str(frame.get("lesson_stage") or "").strip()
            for frame in history
            if str(frame.get("lesson_stage") or "").strip()
        ],
        [str(state.get("lesson_stage") or "").strip()],
    )

    return {
        "storage_strategy": "project_from_conversation_json",
        "needs_dedicated_store": False,
        "reason": (
            "Current analytics needs are served by student_profile_json, "
            "lesson_frame_json, chat_lesson_history snapshots, and raw review tables."
        ),
        "context": context,
        "metrics": {
            "retention_band": metrics.get("retention_band"),
            "review_pressure": metrics.get("review_pressure"),
            "difficulty_signal": metrics.get("difficulty_signal"),
            "recommended_pace": metrics.get("recommended_pace"),
            "recommended_mode": metrics.get("recommended_mode"),
            "cefr_readiness": metrics.get("cefr_readiness"),
        },
        "history": {
            "snapshot_count": len(history),
            "recent_focus_areas": recent_focus_areas,
            "recent_lesson_stages": recent_stages,
        },
    }


def load_cross_mode_learning_context(db: Session, user_id: str, *, mode: str) -> dict[str, Any]:
    """Load the latest pedagogical context so card modes can reuse Chat Coach memory."""
    latest_conversation = (
        db.query(ChatConversation)
        .filter(ChatConversation.user_id == user_id)
        .order_by(ChatConversation.updated_at.desc())
        .first()
    )

    user = db.query(User).filter(User.id == user_id).first()
    pedagogical_metrics = collect_pedagogical_metrics(db, user_id, user=user) if user else {}

    if latest_conversation:
        seeded_profile = dict(latest_conversation.student_profile_json or {})
        if pedagogical_metrics:
            seeded_profile["pedagogical_metrics"] = pedagogical_metrics
        profile, lesson_frame = sync_student_profile_and_lesson_frame(
            seeded_profile,
            dict(latest_conversation.lesson_frame_json or {}),
        )
        return build_learning_context(profile, lesson_frame, mode=mode)

    recent_signals = extract_recent_chat_signals(db, user_id) if user else {}
    profile = build_student_profile(
        user,
        recent_signals=recent_signals,
        pedagogical_metrics=pedagogical_metrics,
    )
    profile, lesson_frame = sync_student_profile_and_lesson_frame(profile, {})
    return build_learning_context(profile, lesson_frame, mode=mode)


def refresh_conversation_learning_state(
    db: Session,
    conversation: ChatConversation,
    teacher_analysis: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Refresh the persisted conversation profile and summary after a teacher analysis."""
    user = db.query(User).filter(User.id == conversation.user_id).first()
    recent_signals = extract_recent_chat_signals(db, str(conversation.user_id)) if user else {}
    pedagogical_metrics = collect_pedagogical_metrics(db, str(conversation.user_id), user=user) if user else {}
    base_profile = build_student_profile(
        user,
        recent_signals=recent_signals,
        seed_profile=conversation.student_profile_json,
        pedagogical_metrics=pedagogical_metrics,
    )
    updated_profile = apply_teacher_analysis_to_profile(
        student_profile=base_profile,
        teacher_analysis=teacher_analysis or {},
        lesson_frame=conversation.lesson_frame_json or {},
    )
    updated_profile, updated_lesson_frame = sync_student_profile_and_lesson_frame(
        updated_profile,
        conversation.lesson_frame_json or {},
    )
    conversation.student_profile_json = updated_profile
    conversation.lesson_frame_json = updated_lesson_frame
    conversation.session_summary = build_session_summary(updated_profile)
    record_lesson_frame_snapshot(db, conversation, updated_lesson_frame)
    return updated_profile, updated_lesson_frame, conversation.session_summary
