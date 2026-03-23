"""Feedback-building helpers for Chat Coach draft evaluation."""

from __future__ import annotations

import random
from typing import List, Optional

from fastapi import WebSocket

from app.core.time import utc_now
from app.models import ChatConversation
from app.schemas.chat import DraftFeedbackOut
from app.services.languagetool_client import LanguageToolClient


async def get_grammar_issues(
    draft_text: str,
    grammar_provider: str,
    grammar_url: str,
) -> List[dict]:
    """Get grammar issues from LanguageTool when enabled."""
    if grammar_provider != "languagetool":
        return []

    if len(draft_text) < 3:
        return []

    try:
        lt_client = LanguageToolClient(base_url=grammar_url)
        lt_issues = await lt_client.check_text(draft_text)
        await lt_client.close()
        return lt_issues
    except Exception:
        return []


def merge_issues(lt_issues: List[dict], heuristic_issues: List[dict]) -> List[dict]:
    """Merge LanguageTool and heuristic issues while deduplicating by span/category."""
    seen = set()
    merged = []

    for issue in lt_issues:
        signature = (
            issue.get("category"),
            issue.get("highlight_spans", [{}])[0].get("start", 0),
            issue.get("highlight_spans", [{}])[0].get("end", 0),
        )
        if signature not in seen:
            seen.add(signature)
            merged.append(issue)

    for issue in heuristic_issues:
        if not issue.get("highlight_spans"):
            merged.append(issue)
            continue

        signature = (
            issue.get("category"),
            issue.get("highlight_spans", [{}])[0].get("start", 0),
            issue.get("highlight_spans", [{}])[0].get("end", 0),
        )
        if signature not in seen:
            seen.add(signature)
            merged.append(issue)

    return merged


def generate_micro_tip(draft: str, lesson_frame: dict) -> str:
    """Generate a light coaching tip when no issues are detected."""
    seed = sum(ord(c) for c in draft) % 100
    rng = random.Random(seed)
    del rng

    draft_lower = draft.lower().strip()
    word_count = len(draft_lower.split())

    if word_count < 5:
        tips = [
            "Good start! Try expanding with more details.",
            "Nice beginning! Can you add more information?",
            "Great! Tell me more about this.",
        ]
        return tips[seed % len(tips)]

    if draft_lower.endswith("?"):
        tips = [
            "Good question! Try asking for more specific details.",
            "Nice! You can also ask about feelings or opinions.",
            "Great question! What made you think about this?",
        ]
        return tips[seed % len(tips)]

    if any(w in draft_lower for w in ["yesterday", "last", "ago", "went", "did"]):
        tips = [
            "Well done! Can you tell me more about it?",
            "Good job! How did you feel about it?",
            "Nice! What happened next?",
        ]
        return tips[seed % len(tips)]

    if any(w in draft_lower for w in ["tomorrow", "will", "going to", "plan"]):
        tips = [
            "Sounds exciting! Any specific preparations?",
            "Great! When will you do this?",
            "Nice! Who will you go with?",
        ]
        return tips[seed % len(tips)]

    if any(w in draft_lower for w in ["like", "love", "enjoy", "favorite"]):
        tips = [
            "That's interesting! How often do you do this?",
            "Nice! What do you like most about it?",
            "Great! Since when have you enjoyed this?",
        ]
        return tips[seed % len(tips)]

    tips = [
        "Great job! Try asking a follow-up question.",
        "Well done! Can you add more details?",
        "Nice! Tell me more about it.",
        "Good! What else would you like to share?",
    ]
    return tips[seed % len(tips)]


def build_draft_feedback(
    conversation_id: str,
    eval_result: dict,
    now_ms: int,
    ghost_suggestion: Optional[str] = None,
    draft: Optional[str] = None,
    lesson_frame: Optional[dict] = None,
) -> dict:
    """Build the `draft_feedback` websocket payload from a micro-eval result."""
    bar_score_raw = (
        eval_result["spelling_score"] * 0.20
        + eval_result["grammar_score"] * 0.25
        + 100 * 0.10
        + eval_result["lesson_alignment_score"] * 0.30
        + eval_result["naturalness_score"] * 0.15
    )

    issues = []
    for issue in eval_result.get("top_issues", []):
        issues.append(
            {
                "category": issue["category"],
                "title": issue["title"],
                "explanation": issue["explanation"],
                "highlight_spans": issue.get("highlight_spans", []),
                "suggestions": issue.get("suggestions", []),
            }
        )

    micro_tip = None
    if not issues and draft:
        micro_tip = generate_micro_tip(draft, lesson_frame or {})

    suggested_next_words = eval_result.get("suggested_next_words", [])
    topic = eval_result.get("topic")
    intent = eval_result.get("intent")

    rewrite = None
    if issues and issues[0].get("suggestions"):
        rewrite = issues[0]["suggestions"][0] if issues[0]["suggestions"] else None

    return DraftFeedbackOut(
        type="draft_feedback",
        conversation_id=conversation_id,
        bar_score_raw=bar_score_raw,
        bar_score_components={
            "spelling": eval_result["spelling_score"],
            "grammar": eval_result["grammar_score"],
            "syntax": 100.0,
            "lesson_alignment": eval_result["lesson_alignment_score"],
            "naturalness": eval_result["naturalness_score"],
        },
        lesson_alignment_score=eval_result["lesson_alignment_score"],
        issues=issues,
        ghost_suggestion=ghost_suggestion,
        micro_tip=micro_tip,
        suggested_next_words=suggested_next_words,
        topic=topic,
        intent=intent,
        rewrite=rewrite,
        draft=draft or "",
        server_ts_ms=now_ms,
    ).model_dump()


async def evaluate_draft_feedback(
    conversation: ChatConversation,
    draft_text: str,
    now_ms: int,
    llm_provider,
    grammar_provider: str,
    grammar_url: str,
    ghost_suggestion: Optional[str] = None,
    include_grammar_check: bool = False,
) -> dict:
    """Run micro-eval and optional grammar-checking, then build the payload."""
    lt_issues: List[dict] = []
    if include_grammar_check:
        lt_issues = await get_grammar_issues(
            draft_text=draft_text,
            grammar_provider=grammar_provider,
            grammar_url=grammar_url,
        )

    eval_result = await llm_provider.micro_eval(
        context=conversation.session_summary,
        lesson_frame=conversation.lesson_frame_json,
        draft=draft_text,
        student_profile=conversation.student_profile_json,
    )

    if lt_issues:
        heuristic_issues = eval_result.get("top_issues", [])
        eval_result["top_issues"] = merge_issues(lt_issues, heuristic_issues)

    return build_draft_feedback(
        conversation_id=str(conversation.id),
        eval_result=eval_result,
        now_ms=now_ms,
        ghost_suggestion=ghost_suggestion,
        draft=draft_text,
        lesson_frame=conversation.lesson_frame_json,
    )


async def freeze_user_message_feedback(
    websocket: WebSocket,
    conversation: ChatConversation,
    content: str,
    chat_provider,
) -> dict:
    """Evaluate and emit the frozen feedback snapshot for a submitted message."""
    eval_result = await chat_provider.micro_eval(
        context=conversation.session_summary,
        lesson_frame=conversation.lesson_frame_json,
        draft=content,
        student_profile=conversation.student_profile_json,
    )

    feedback = build_draft_feedback(
        conversation_id=str(conversation.id),
        eval_result=eval_result,
        now_ms=int(utc_now().timestamp() * 1000),
        ghost_suggestion=None,
        draft=content,
        lesson_frame=conversation.lesson_frame_json,
    )
    await websocket.send_json(feedback)
    return feedback
