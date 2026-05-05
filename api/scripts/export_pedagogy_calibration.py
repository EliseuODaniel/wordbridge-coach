"""Export pedagogical calibration signals for real-use review.

The output is intentionally read-only and JSON-shaped so it can be compared
across small real sessions without adding an analytics endpoint or table yet.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import desc

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.core.database import SessionLocal
from app.models import ChatConversation, ChatLessonHistory, User
from app.services.chat_profile_service import (
    build_pedagogical_analytics_projection,
    collect_pedagogical_metrics,
    sync_student_profile_and_lesson_frame,
)

LANGUAGE_NAMES = {
    "en": "English",
    "pt": "Portuguese",
    "es": "Spanish",
    "fr": "French",
}


def _json_default(value: Any) -> str:
    return str(value)


def _resolve_user(db, *, user_id: str | None, username: str | None) -> User | None:
    query = db.query(User)
    if user_id:
        return query.filter(User.id == user_id).first()
    if username:
        return query.filter(User.username == username).first()
    return query.order_by(desc(User.created_at)).first()


def _latest_conversation(db, user_id: str) -> ChatConversation | None:
    return (
        db.query(ChatConversation)
        .filter(ChatConversation.user_id == user_id)
        .order_by(desc(ChatConversation.updated_at), desc(ChatConversation.created_at))
        .first()
    )


def _lesson_history(db, conversation_id: str, limit: int) -> list[dict[str, Any]]:
    rows = (
        db.query(ChatLessonHistory)
        .filter(ChatLessonHistory.conversation_id == conversation_id)
        .order_by(desc(ChatLessonHistory.created_at))
        .limit(limit)
        .all()
    )
    return [dict(row.lesson_frame_json or {}) for row in reversed(rows)]


def _language_code(user: User, relationship_name: str, fallback: str) -> str:
    language = getattr(user, relationship_name, None)
    code = getattr(language, "code", None)
    return str(code or fallback).lower()


def _base_student_profile(user: User, metrics: dict[str, Any]) -> dict[str, Any]:
    feedback_code = str(getattr(user, "language_preference", None) or "en").lower()
    target_code = _language_code(user, "target_language_obj", "en")
    return {
        "feedback_language": LANGUAGE_NAMES.get(feedback_code, feedback_code),
        "target_language": LANGUAGE_NAMES.get(target_code, target_code),
        "mode": getattr(user, "mode", "spec4"),
        "pedagogical_metrics": metrics,
    }


def build_calibration_export(
    *,
    user_id: str | None = None,
    username: str | None = None,
    history_limit: int = 8,
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        user = _resolve_user(db, user_id=user_id, username=username)
        if not user:
            return {
                "status": "empty",
                "reason": "No user found. Create or select a profile before exporting calibration signals.",
            }

        metrics = collect_pedagogical_metrics(db, str(user.id), user=user)
        conversation = _latest_conversation(db, str(user.id))
        if conversation:
            student_profile = {
                **_base_student_profile(user, metrics),
                **dict(conversation.student_profile_json or {}),
                "pedagogical_metrics": metrics,
            }
            student_profile, lesson_frame = sync_student_profile_and_lesson_frame(
                student_profile,
                dict(conversation.lesson_frame_json or {}),
            )
            history = _lesson_history(db, str(conversation.id), history_limit)
            mode = str(getattr(user, "mode", None) or metrics.get("recommended_mode") or "spec4")
        else:
            student_profile = _base_student_profile(user, metrics)
            student_profile, lesson_frame = sync_student_profile_and_lesson_frame(student_profile, {})
            history = []
            mode = str(getattr(user, "mode", None) or "spec4")

        projection = build_pedagogical_analytics_projection(
            student_profile,
            lesson_frame,
            mode=mode,
            lesson_history=history,
        )

        return {
            "status": "ok",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "target_language": _language_code(user, "target_language_obj", "en"),
                "language_preference": user.language_preference,
                "word_goal_rank": user.word_goal_rank,
                "mode": mode,
            },
            "calibration_focus": {
                "retention_band": metrics.get("retention_band"),
                "review_pressure": metrics.get("review_pressure"),
                "recommended_pace": metrics.get("recommended_pace"),
                "recommended_mode": metrics.get("recommended_mode"),
                "difficulty_signal": metrics.get("difficulty_signal"),
            },
            "raw_metrics": metrics,
            "projection": projection,
        }
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export WordBridge pedagogical calibration signals.")
    parser.add_argument("--user-id", help="User UUID to export. Defaults to latest user when omitted.")
    parser.add_argument("--username", help="Username to export. Ignored when --user-id is provided.")
    parser.add_argument("--history-limit", type=int, default=8, help="Number of lesson-frame snapshots to include.")
    parser.add_argument("--output", help="Optional path to write the JSON export.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_calibration_export(
        user_id=args.user_id,
        username=args.username,
        history_limit=max(0, args.history_limit),
    )
    encoded = json.dumps(payload, indent=2, sort_keys=True, default=_json_default)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"{encoded}\n", encoding="utf-8")
    else:
        print(encoded)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
