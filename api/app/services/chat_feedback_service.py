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


def infer_highlight_spans(issue: dict, draft_text: str) -> list[dict]:
    """Infer spans from highlight_text when the provider omits explicit offsets."""
    existing_spans = issue.get("highlight_spans") or []
    if existing_spans:
        return existing_spans

    highlight_text = (issue.get("highlight_text") or "").strip()
    if not highlight_text or not draft_text:
        return []

    draft_lower = draft_text.lower()
    highlight_lower = highlight_text.lower()
    start = draft_lower.find(highlight_lower)
    if start < 0:
        return []

    return [{"start": start, "end": start + len(highlight_text)}]


def merge_issues(lt_issues: List[dict], heuristic_issues: List[dict]) -> List[dict]:
    """Merge LanguageTool and heuristic issues while deduplicating by span/category."""
    def build_issue_signature(issue: dict):
        spans = issue.get("highlight_spans") or []
        if spans:
            return (
                issue.get("category"),
                spans[0].get("start", 0),
                spans[0].get("end", 0),
            )

        highlight_text = (issue.get("highlight_text") or "").strip().lower()
        if highlight_text:
            return (
                issue.get("category"),
                highlight_text,
            )

        return None

    seen = set()
    merged = []

    for issue in lt_issues:
        signature = build_issue_signature(issue)
        if signature is None or signature not in seen:
            if signature is not None:
                seen.add(signature)
            merged.append(issue)

    for issue in heuristic_issues:
        signature = build_issue_signature(issue)
        if signature is None or signature not in seen:
            if signature is not None:
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
    seen_issue_signatures = set()
    for issue in eval_result.get("top_issues", []):
        highlight_spans = infer_highlight_spans(issue, draft or "")
        if highlight_spans:
            signature = (
                issue["category"],
                highlight_spans[0]["start"],
                highlight_spans[0]["end"],
            )
        else:
            signature = (
                issue["category"],
                issue.get("highlight_text", ""),
            )
        if signature in seen_issue_signatures:
            continue
        seen_issue_signatures.add(signature)
        issues.append(
            {
                "category": issue["category"],
                "title": issue["title"],
                "explanation": issue["explanation"],
                "highlight_spans": highlight_spans,
                "suggestions": issue.get("suggestions", []),
            }
        )

    micro_tip = eval_result.get("micro_tip")
    if not micro_tip and not issues and draft:
        micro_tip = generate_micro_tip(draft, lesson_frame or {})

    suggested_next_words = eval_result.get("suggested_next_words", [])
    topic = eval_result.get("topic")
    intent = eval_result.get("intent")
    self_check_prompt = eval_result.get("self_check_prompt")
    encouragement = eval_result.get("encouragement")

    rewrite = None
    if eval_result.get("rewrite"):
        rewrite = eval_result["rewrite"]
    elif issues and issues[0].get("suggestions"):
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
        self_check_prompt=self_check_prompt,
        encouragement=encouragement,
        suggested_next_words=suggested_next_words,
        topic=topic,
        intent=intent,
        rewrite=rewrite,
        draft=draft or "",
        server_ts_ms=now_ms,
    ).model_dump()


def build_realtime_draft_evaluation(
    grammar_issues: List[dict],
    lesson_frame: dict,
) -> dict:
    """Build bounded live feedback without occupying the generative LLM."""
    issues = grammar_issues[:3]
    spelling_count = sum(issue.get("category") == "spelling" for issue in issues)
    grammar_count = sum(issue.get("category") in {"grammar", "syntax"} for issue in issues)
    style_count = sum(issue.get("category") == "style" for issue in issues)

    return {
        "spelling_score": max(0.0, 100.0 - spelling_count * 20.0),
        "grammar_score": max(0.0, 100.0 - grammar_count * 20.0),
        "lesson_alignment_score": 100.0,
        "naturalness_score": max(0.0, 100.0 - style_count * 10.0),
        "top_issues": issues,
        "suggested_next_words": [],
        "topic": lesson_frame.get("topic"),
        "intent": lesson_frame.get("expected_intent"),
    }


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
    """Build low-latency live feedback; rich LLM analysis runs after submission."""
    del llm_provider

    lt_issues: List[dict] = []
    if include_grammar_check:
        lt_issues = await get_grammar_issues(
            draft_text=draft_text,
            grammar_provider=grammar_provider,
            grammar_url=grammar_url,
        )

    eval_result = build_realtime_draft_evaluation(
        grammar_issues=lt_issues,
        lesson_frame=conversation.lesson_frame_json,
    )

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
