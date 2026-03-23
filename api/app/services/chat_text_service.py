"""Pure text and generation-config helpers for Chat Coach."""

from __future__ import annotations

import re
from typing import List


def build_chat_system_prompt(lesson_frame: dict) -> str:
    """Build the chat tutor system prompt from the current lesson frame."""
    return f"""You are an English tutor helping a {lesson_frame.get('cefr_target', 'A2')} student.
Topic: {lesson_frame.get('topic', 'conversation')}
Goal: {lesson_frame.get('learning_goal', 'practice conversation')}

Keep it natural:
- Reply briefly (1-3 sentences) as if chatting with a friend
- Always ask a follow-up question
- Never correct grammar or explain rules
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
        "next_practice": [],
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
