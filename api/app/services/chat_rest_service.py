"""REST-side lookup and serialization helpers for Chat Coach."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import ChatConversation, ChatMessage, User
from app.schemas.chat import ChatConversationResponse, ChatMessageResponse


def get_user_or_404(db: Session, user_id: str) -> User:
    """Load a user or raise a standardized 404 error."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "User not found", "message": f"User '{user_id}' not found"},
        )
    return user


def get_conversation_or_404(db: Session, conversation_id: str) -> ChatConversation:
    """Load a conversation or raise a standardized 404 error."""
    conversation = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id
    ).first()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Conversation not found", "message": f"Conversation '{conversation_id}' not found"},
        )
    return conversation


def serialize_conversation(conversation: ChatConversation) -> ChatConversationResponse:
    """Convert a ChatConversation model into the REST response schema."""
    return ChatConversationResponse(
        id=str(conversation.id),
        user_id=str(conversation.user_id),
        title=conversation.title,
        student_profile_json=conversation.student_profile_json,
        lesson_frame_json=conversation.lesson_frame_json,
        session_summary=conversation.session_summary,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def serialize_message(message: ChatMessage) -> ChatMessageResponse:
    """Convert a ChatMessage model into the REST response schema."""
    return ChatMessageResponse(
        id=str(message.id),
        conversation_id=str(message.conversation_id),
        role=message.role,
        content=message.content,
        metadata_json=message.metadata_json,
        created_at=message.created_at,
    )


def serialize_conversation_list_item(db: Session, conversation: ChatConversation) -> dict:
    """Build the list payload for a conversation including message count."""
    message_count = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation.id
    ).count()

    return {
        "id": str(conversation.id),
        "user_id": str(conversation.user_id),
        "title": conversation.title,
        "student_profile_json": conversation.student_profile_json,
        "lesson_frame_json": conversation.lesson_frame_json,
        "session_summary": conversation.session_summary,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "message_count": message_count,
    }
