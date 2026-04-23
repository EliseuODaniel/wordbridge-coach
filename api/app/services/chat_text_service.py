"""Pure text and generation-config helpers for Chat Coach."""

from __future__ import annotations

import re
from typing import Any, List


def build_chat_system_prompt(
    lesson_frame: dict,
    student_profile: dict[str, Any] | None = None,
    session_summary: str = "",
) -> str:
    """Build the chat tutor system prompt from the current lesson frame."""
    student_profile = student_profile or {}
    cefr_target = lesson_frame.get("cefr_target") or student_profile.get("cefr_level", "A2")
    feedback_language = student_profile.get("feedback_language", "English")
    target_language = student_profile.get("target_language", "English")
    scaffolding_level = str(student_profile.get("scaffolding_level", "guided_practice")).replace("_", " ")
    strengths = ", ".join(student_profile.get("strengths", [])[:2]) or "none recorded yet"
    focus_areas = ", ".join(
        (student_profile.get("weaknesses") or student_profile.get("common_errors") or [])[:2]
    ) or "clear communication"
    pedagogical_metrics = dict(student_profile.get("pedagogical_metrics") or {})
    longitudinal_memory = session_summary or "No prior learner memory yet."

    return f"""You are an English tutor helping a {cefr_target} student practice {target_language}.
Topic: {lesson_frame.get('topic', 'conversation')}
Goal: {lesson_frame.get('learning_goal', 'practice conversation')}

Coaching memory:
- Feedback language for explanations: {feedback_language}
- Scaffolding: {scaffolding_level}
- Recent strengths: {strengths}
- Current focus: {focus_areas}
- Retention signal: {pedagogical_metrics.get('retention_band', 'unknown')}
- Difficulty signal: {pedagogical_metrics.get('difficulty_signal', 'on_target')}
- Review pressure: {pedagogical_metrics.get('review_pressure', 'medium')}
- Recommended pace: {pedagogical_metrics.get('recommended_pace', 'balance')}
- Longitudinal summary: {longitudinal_memory}

Keep it natural:
- Reply briefly (1-3 sentences) as if chatting with a friend
- Always ask a follow-up question
- Match the challenge to the student's CEFR and scaffolding level
- Build follow-up questions from the topic or current focus area when possible
- Never proactively correct grammar or explain rules
- If they write in Portuguese/Spanish, encourage them to use English
- No examples, quotes, or meta-commentary
"""


def get_chat_stop_sequences() -> List[str]:
    """Return sanitized stop sequences for chat generation."""
    stop_sequences = [
        '\n\n"',
        '\nUser:', '\nUSER:', '\nStudent:', '\nSTUDENT:',
        '">', '<|',
        '\n\nCRITICAL INSTRUCTIONS',
        '\nNote:', '\n(Note:', '\nTeacher:', '\nAnalysis:',
        '\nExplanation:', '\nCorrection:', '\nMeta:', '\nSystem:',
    ]
    return [sequence for sequence in stop_sequences if isinstance(sequence, str) and sequence.strip()]


def build_chat_generation_config() -> dict:
    """Return the default generation config for chat replies."""
    return {
        "temperature": 0.5,
        "max_tokens": 300,
        "top_p": 0.9,
        "stop": get_chat_stop_sequences(),
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    }


def build_teacher_analysis_fallback(error: Exception) -> dict:
    """Build the fallback payload used when teacher analysis generation fails."""
    error_reason = str(error)[:100]
    return {
        "teacher_summary": f"Teacher analysis failed: {error_reason}",
        "rewrite": None,
        "corrections": [],
        "strengths": [],
        "focus_areas": [],
        "next_practice": [],
        "reflection_question": None,
        "encouragement": None,
        "debug_reason": error_reason,
    }


def sanitize_assistant_response(response: str) -> str:
    """Remove meta-commentary and extra user simulation from LLM response."""
    response = re.sub(r'\(Note:[^)]*\)', '', response, flags=re.IGNORECASE)
    response = re.sub(r'\(Teacher:[^)]*\)', '', response, flags=re.IGNORECASE)
    response = re.sub(r'\(Analysis:[^)]*\)', '', response, flags=re.IGNORECASE)
    response = re.sub(r'\(Correction:[^)]*\)', '', response, flags=re.IGNORECASE)

    filtered_lines = []
    for line in response.split('\n'):
        stripped = line.strip()
        if re.match(r'^(Note|Teacher|Analysis|Explanation|Correction|Meta|System):', stripped, re.IGNORECASE):
            continue
        filtered_lines.append(line)

    response = '\n'.join(filtered_lines)

    truncated_lines = []
    for line in response.split('\n'):
        if 'CRITICAL INSTRUCTIONS' in line:
            break
        truncated_lines.append(line)

    response = '\n'.join(truncated_lines)
    response = re.sub(r'\n\s*\n"[\s\S]*"\s*$', '', response).strip()

    lines = response.split('\n')
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(('User:', 'USER:', 'Student:', 'STUDENT:')):
            lines = lines[:index]
            break

    return '\n'.join(lines).strip()
