"""Conversation management helpers extracted from the Chat Coach endpoint."""

from __future__ import annotations

from app.models import ChatConversation, ChatMessage
from app.services.chat_profile_service import build_seed_chat_state, record_lesson_frame_snapshot
from app.services.chat_rest_service import (
    get_conversation_or_404,
    get_user_or_404,
    serialize_conversation,
    serialize_conversation_list_item,
    serialize_message,
)


def get_default_lesson_frame() -> dict:
    """Return the default lesson frame for new conversations."""
    return {
        "cefr_target": "A2",
        "learning_goal": "conversation_start",
        "expected_intent": "introduction",
        "topic": "getting_started",
        "rubric": {
            "grammar": [],
            "vocab": [],
            "style": ["friendly"],
        },
        "scoring_hints": {
            "avoid": [],
            "encourage": ["complete_sentences", "clear_communication"],
        },
    }


def get_default_student_profile() -> dict:
    """Return the default student profile for new conversations."""
    return {
        "cefr_level": "A2",
        "common_errors": [],
        "strengths": [],
        "weaknesses": [],
    }


def build_system_message_content(lesson_frame: dict, student_profile: dict | None = None) -> str:
    """Build the default system message persisted for a new conversation."""
    cefr_target = lesson_frame.get("cefr_target", "A2")
    student_profile = student_profile or {}
    feedback_language = student_profile.get("feedback_language", "English")
    target_language = student_profile.get("target_language", "English")
    return (
        f"You are an expert teacher of {target_language} helping a learner at the "
        f"{cefr_target} instructional band practice conversation. "
        f"Use {feedback_language} for explicit feedback when needed."
    )


def create_chat_conversation(db, conversation_data):
    """Create a conversation plus its initial system message."""
    user = get_user_or_404(db, conversation_data.user_id)
    student_profile, lesson_frame, session_summary = build_seed_chat_state(
        db,
        user,
        base_lesson_frame=get_default_lesson_frame(),
    )

    conversation = ChatConversation(
        user_id=conversation_data.user_id,
        title=conversation_data.title,
        student_profile_json=student_profile,
        lesson_frame_json=lesson_frame,
        session_summary=session_summary,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    system_message = ChatMessage(
        conversation_id=conversation.id,
        role="system",
        content=build_system_message_content(
            conversation.lesson_frame_json,
            conversation.student_profile_json,
        ),
    )
    record_lesson_frame_snapshot(db, conversation, conversation.lesson_frame_json)
    db.add(system_message)
    db.commit()

    return serialize_conversation(conversation)


def list_chat_conversations(db, user_id: str):
    """List serialized conversations ordered by last update."""
    get_user_or_404(db, user_id)

    conversations = (
        db.query(ChatConversation)
        .filter(ChatConversation.user_id == user_id)
        .order_by(ChatConversation.updated_at.desc())
        .all()
    )
    return [serialize_conversation_list_item(db, conversation) for conversation in conversations]


def list_chat_messages(db, conversation_id: str, *, limit: int = 100, offset: int = 0):
    """List serialized messages for a conversation."""
    get_conversation_or_404(db, conversation_id)

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [serialize_message(message) for message in messages]


def delete_chat_conversation(db, conversation_id: str):
    """Delete a conversation and rely on cascade for its messages."""
    conversation = get_conversation_or_404(db, conversation_id)
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted successfully"}
