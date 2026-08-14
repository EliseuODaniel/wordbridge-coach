from app.services.chat_text_service import (
    build_chat_generation_config,
    build_chat_system_prompt,
    build_teacher_analysis_fallback,
    sanitize_assistant_response,
)


def test_build_chat_system_prompt_uses_lesson_frame_defaults():
    prompt = build_chat_system_prompt({
        "cefr_target": "B1",
        "topic": "travel",
        "learning_goal": "asking_for_directions",
    }, {
        "feedback_language": "Portuguese",
        "strengths": ["Clear openings"],
        "weaknesses": ["Past tense"],
        "scaffolding_level": "guided_practice",
        "pedagogical_metrics": {
            "retention_band": "building",
            "difficulty_signal": "on_target",
            "review_pressure": "medium",
            "recommended_pace": "balance",
        },
    }, "Longitudinal learner profile")

    assert "B1" in prompt
    assert "travel" in prompt
    assert "asking_for_directions" in prompt
    assert "Always ask a follow-up question" in prompt
    assert "Portuguese" in prompt
    assert "Longitudinal learner profile" in prompt
    assert "Retention signal: building" in prompt
    assert "Review pressure: medium" in prompt
    assert "No examples, quotes, or meta-commentary" in prompt
    assert "instructional band, not a certification claim" in prompt
    assert "a separate evaluator handles every language correction" in prompt
    assert "respond only to the meaning" in prompt


def test_build_chat_system_prompt_does_not_hardcode_english():
    prompt = build_chat_system_prompt(
        {"cefr_target": "A2", "topic": "travel", "learning_goal": "directions"},
        {
            "target_language": "French",
            "feedback_language": "Portuguese",
            "scaffolding_level": "guided_practice",
        },
    )
    assert "expert French tutor" in prompt
    assert "Stay in French" in prompt
    assert "encourage them to use English" not in prompt
    assert "content-focused follow-up" in prompt
    assert "leave language feedback separate" in prompt


def test_build_chat_generation_config_filters_stop_sequences():
    config = build_chat_generation_config()

    assert config["temperature"] == 0.5
    assert config["max_tokens"] == 300
    assert "\nUser:" in config["stop"]
    assert "\nSystem:" in config["stop"]
    assert all(isinstance(stop, str) and stop.strip() for stop in config["stop"])


def test_build_teacher_analysis_fallback_truncates_error_reason():
    long_error = RuntimeError("x" * 150)
    fallback = build_teacher_analysis_fallback(long_error)

    assert fallback["rewrite"] is None
    assert fallback["corrections"] == []
    assert fallback["strengths"] == []
    assert fallback["focus_areas"] == []
    assert fallback["next_practice"] == []
    assert fallback["reflection_question"] is None
    assert fallback["encouragement"] is None
    assert len(fallback["debug_reason"]) == 100
    assert fallback["teacher_summary"].startswith("Teacher analysis failed:")


def test_sanitize_assistant_response_removes_quoted_user_simulation():
    response = "That's great! How was your experience?\n\n\"I went to the beach and it was fun.\""
    sanitized = sanitize_assistant_response(response)

    assert "I went to the beach" not in sanitized
    assert sanitized == "That's great! How was your experience?"


def test_sanitize_assistant_response_truncates_at_role_labels():
    response = "That's interesting! Tell me more.\nUser: I went to the park yesterday."
    sanitized = sanitize_assistant_response(response)

    assert "I went to the park" not in sanitized
    assert sanitized == "That's interesting! Tell me more."
