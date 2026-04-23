"""Prompt and schema helpers for pedagogical structured-output LLM tasks."""

from __future__ import annotations

import json
from typing import Any, Type

from pydantic import BaseModel, ConfigDict, Field


class PedagogicalIssue(BaseModel):
    """Single issue found in a learner draft."""

    model_config = ConfigDict(extra="forbid")

    category: str = Field(
        ...,
        description="One of spelling, grammar, syntax, semantic, or style.",
    )
    title: str = Field(..., description="Short label for the issue.")
    explanation: str = Field(..., description="Why it matters, in learner-friendly language.")
    highlight_text: str = Field(
        default="",
        description="Exact substring from the student's draft when possible.",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Up to three short suggested fixes or better options.",
    )


class DraftEvaluationPayload(BaseModel):
    """Structured payload used for draft evaluation."""

    model_config = ConfigDict(extra="forbid")

    grammar_score: float = Field(..., ge=0, le=100)
    spelling_score: float = Field(..., ge=0, le=100)
    naturalness_score: float = Field(..., ge=0, le=100)
    lesson_alignment_score: float = Field(..., ge=0, le=100)
    top_issues: list[PedagogicalIssue] = Field(default_factory=list)
    suggested_next_words: list[str] = Field(default_factory=list)
    micro_tip: str = Field(
        default="",
        description="A brief cognitive hint to help the learner improve the draft.",
    )
    self_check_prompt: str = Field(
        default="",
        description="A metacognitive prompt that encourages self-correction.",
    )
    encouragement: str = Field(
        default="",
        description="A short motivational message grounded in the student's actual attempt.",
    )
    topic: str = Field(default="")
    intent: str = Field(default="")
    rewrite: str = Field(
        default="",
        description="A concise model rewrite when it truly helps the learner.",
    )


class AutocompletePayload(BaseModel):
    """Structured payload used for ghost suggestions."""

    model_config = ConfigDict(extra="forbid")

    ghost_suggestion: str = Field(
        ...,
        description="A continuation of one to six words, not a full completed answer.",
    )
    reason: str = Field(
        ...,
        description="Short explanation of the continuation choice for observability/debugging.",
    )


class TeacherCorrection(BaseModel):
    """Correction item for the teacher analysis."""

    model_config = ConfigDict(extra="forbid")

    mistake: str = Field(..., description="Original learner wording or fragment.")
    fix: str = Field(..., description="Corrected wording.")
    why: str = Field(..., description="Short explanation of the correction.")


class TeacherAnalysisPayload(BaseModel):
    """Structured pedagogical analysis emitted after a learner turn."""

    model_config = ConfigDict(extra="forbid")

    rewrite: str = Field(default="")
    corrections: list[TeacherCorrection] = Field(default_factory=list)
    teacher_summary: str = Field(
        ...,
        description="Main formative feedback message for the learner.",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="What the learner already did well in this turn.",
    )
    focus_areas: list[str] = Field(
        default_factory=list,
        description="Small set of concrete next focus areas.",
    )
    next_practice: list[str] = Field(
        default_factory=list,
        description="Two or three short targeted drills or prompts.",
    )
    reflection_question: str = Field(
        default="",
        description="One question that helps the learner reflect before the next reply.",
    )
    encouragement: str = Field(
        default="",
        description="A short motivational line tied to the current attempt.",
    )


def _json_block(payload: dict[str, Any]) -> str:
    """Dump helper for deterministic prompt rendering."""
    return json.dumps(payload or {}, ensure_ascii=False, indent=2, sort_keys=True)


def _feedback_language(student_profile: dict[str, Any]) -> str:
    return str(student_profile.get("feedback_language") or "English")


def _target_language(student_profile: dict[str, Any]) -> str:
    return str(student_profile.get("target_language") or "English")


def build_micro_eval_messages(
    *,
    context: str,
    lesson_frame: dict[str, Any],
    draft: str,
    student_profile: dict[str, Any],
) -> list[dict[str, str]]:
    """Build chat-completion messages for pedagogical draft evaluation."""
    feedback_language = _feedback_language(student_profile)
    target_language = _target_language(student_profile)
    return [
        {
            "role": "system",
            "content": (
                "You are an expert English tutor generating formative feedback for one learner draft. "
                "Return only structured JSON. Keep feedback short, specific, and didactic.\n"
                "Pedagogy rules:\n"
                "- Prefer scaffolding over giving the full answer.\n"
                "- Max 3 issues.\n"
                "- Use highlight_text only when it is an exact substring of the draft.\n"
                "- Keep suggestions short and actionable.\n"
                "- Use self_check_prompt to help the learner notice the issue themselves.\n"
                "- Use encouragement only when grounded in the learner's actual attempt.\n"
                f"- explanations, micro_tip, self_check_prompt, and encouragement must be in {feedback_language}.\n"
                f"- suggestions, suggested_next_words, and rewrite must stay in {target_language}.\n"
                "- If the draft is already good, top_issues may be empty."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Student profile:\n{_json_block(student_profile)}\n\n"
                f"Lesson frame:\n{_json_block(lesson_frame)}\n\n"
                f"Recent context:\n{context or '(empty)'}\n\n"
                f"Student draft:\n{draft}"
            ),
        },
    ]


def build_autocomplete_messages(
    *,
    context: str,
    lesson_frame: dict[str, Any],
    draft: str,
    student_profile: dict[str, Any],
) -> list[dict[str, str]]:
    """Build chat-completion messages for short ghost suggestions."""
    target_language = _target_language(student_profile)
    return [
        {
            "role": "system",
            "content": (
                "You are an English tutor producing a ghost suggestion while the learner types. "
                "Return only structured JSON.\n"
                "Rules:\n"
                "- ghost_suggestion must be 1 to 6 words.\n"
                "- Do not finish the entire sentence if that removes learner effort.\n"
                "- Keep the continuation aligned with the learner CEFR level and current lesson goal.\n"
                f"- ghost_suggestion must stay in {target_language}.\n"
                "- Avoid punctuation-heavy continuations unless the draft clearly needs it."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Student profile:\n{_json_block(student_profile)}\n\n"
                f"Lesson frame:\n{_json_block(lesson_frame)}\n\n"
                f"Recent context:\n{context or '(empty)'}\n\n"
                f"Current draft:\n{draft}"
            ),
        },
    ]


def build_teacher_analysis_messages(
    *,
    user_message: str,
    context: str,
    lesson_frame: dict[str, Any],
    student_profile: dict[str, Any],
) -> list[dict[str, str]]:
    """Build chat-completion messages for post-turn teacher analysis."""
    feedback_language = _feedback_language(student_profile)
    target_language = _target_language(student_profile)
    return [
        {
            "role": "system",
            "content": (
                "You are an expert English teacher reviewing one student message after a live chat turn. "
                "Return only structured JSON.\n"
                "Pedagogy rules:\n"
                "- Do not overwhelm the learner.\n"
                "- strengths and focus_areas should each have at most 3 items.\n"
                "- reflection_question should encourage self-explanation or self-correction.\n"
                "- encouragement must be specific, not generic praise.\n"
                "- next_practice should contain short, targeted drills or prompts.\n"
                f"- teacher_summary, strengths, focus_areas, reflection_question, encouragement, and corrections[].why must be in {feedback_language}.\n"
                f"- rewrite, corrections[].mistake, corrections[].fix, and next_practice must stay in {target_language}.\n"
                "- Use rewrite only when it clarifies the feedback."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Student profile:\n{_json_block(student_profile)}\n\n"
                f"Lesson frame:\n{_json_block(lesson_frame)}\n\n"
                f"Teacher-only context:\n{context or '(empty)'}\n\n"
                f"Student message:\n{user_message}"
            ),
        },
    ]


def build_llamacpp_response_format(model: Type[BaseModel]) -> dict[str, Any]:
    """Build llama.cpp-compatible response_format config."""
    return {
        "type": "json_schema",
        "schema": model.model_json_schema(),
    }


def build_openai_response_format(name: str, model: Type[BaseModel]) -> dict[str, Any]:
    """Build OpenAI-compatible response_format config."""
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": model.model_json_schema(),
        },
    }
