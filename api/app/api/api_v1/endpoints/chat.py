"""Chat Coach endpoints for real-time conversational training"""

import os
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.models import User, ChatConversation, ChatMessage
from app.schemas.chat import (
    ChatConversationCreate,
    ChatConversationResponse,
    ChatMessageResponse,
    DraftFeedbackOut,
    AssistantStreamTokenOut,
    AssistantDoneOut,
    ErrorOut,
    Pong,
)
from app.llm.factory import get_llm_provider_from_env, get_provider_name

# Feature flags (environment variables)
CHAT_LLM_PROVIDER = os.getenv("CHAT_LLM_PROVIDER", "llamacpp")
CHAT_MICRO_EVAL_MIN_INTERVAL_MS = int(os.getenv("CHAT_MICRO_EVAL_MIN_INTERVAL_MS", "90"))

router = APIRouter()

# Initialize LLM provider from environment variables (supports Mock, OpenAI, LlamaCpp)
llm_provider = get_llm_provider_from_env()

# Log which provider is being used (for debugging)
logger.info(f"Chat Coach LLM provider: {get_provider_name(llm_provider)}")

# In-memory tracking for throttling micro_eval (conversation_id -> last_eval_ts)
_micro_eval_timestamps = {}


def get_default_lesson_frame() -> dict:
    """Get default lesson frame for new conversations"""
    return {
        "cefr_target": "A2",
        "learning_goal": "conversation_start",
        "expected_intent": "introduction",
        "topic": "getting_started",
        "rubric": {
            "grammar": [],
            "vocab": [],
            "style": ["friendly"]
        },
        "scoring_hints": {
            "avoid": [],
            "encourage": ["complete_sentences", "clear_communication"]
        }
    }


def get_default_student_profile() -> dict:
    """Get default student profile"""
    return {
        "cefr_level": "A2",
        "common_errors": [],
        "strengths": [],
        "weaknesses": []
    }


def _generate_micro_tip(draft: str, lesson_frame: dict) -> str:
    """
    Generate a helpful tip when no issues are detected.

    Provides contextual encouragement and suggests next steps.

    Args:
        draft: User's draft text
        lesson_frame: Current lesson frame

    Returns:
        Helpful tip message
    """
    import random

    # Create stable random based on draft content
    seed = sum(ord(c) for c in draft) % 100
    rng = random.Random(seed)

    # Detect draft characteristics
    draft_lower = draft.lower().strip()
    word_count = len(draft_lower.split())

    # Very short drafts (< 5 words)
    if word_count < 5:
        tips = [
            "Good start! Try expanding with more details.",
            "Nice beginning! Can you add more information?",
            "Great! Tell me more about this.",
        ]
        return tips[seed % len(tips)]

    # Questions (encourage elaboration)
    if draft_lower.endswith("?"):
        tips = [
            "Good question! Try asking for more specific details.",
            "Nice! You can also ask about feelings or opinions.",
            "Great question! What made you think about this?",
        ]
        return tips[seed % len(tips)]

    # Past tense (encourage follow-up)
    if any(w in draft_lower for w in ["yesterday", "last", "ago", "went", "did"]):
        tips = [
            "Well done! Can you tell me more about it?",
            "Good job! How did you feel about it?",
            "Nice! What happened next?",
        ]
        return tips[seed % len(tips)]

    # Future tense (encourage planning)
    if any(w in draft_lower for w in ["tomorrow", "will", "going to", "plan"]):
        tips = [
            "Sounds exciting! Any specific preparations?",
            "Great! When will you do this?",
            "Nice! Who will you go with?",
        ]
        return tips[seed % len(tips)]

    # Hobbies/likes (encourage elaboration)
    if any(w in draft_lower for w in ["like", "love", "enjoy", "favorite"]):
        tips = [
            "That's interesting! How often do you do this?",
            "Nice! What do you like most about it?",
            "Great! Since when have you enjoyed this?",
        ]
        return tips[seed % len(tips)]

    # Default encouragement
    tips = [
        "Great job! Try asking a follow-up question.",
        "Well done! Can you add more details?",
        "Nice! Tell me more about it.",
        "Good! What else would you like to share?",
    ]
    return tips[seed % len(tips)]


def _build_draft_feedback(
    conversation_id: str,
    eval_result: dict,
    now_ms: int,
    ghost_suggestion: str = None,
    draft: str = None,
    lesson_frame: dict = None
) -> dict:
    """
    Build draft_feedback response from micro_eval result.

    Calculates bar score, maps issues, optionally includes ghost suggestion,
    and generates micro_tip when no issues are detected.

    Args:
        conversation_id: UUID of the conversation
        eval_result: Result from llm_provider.micro_eval()
        now_ms: Current timestamp in milliseconds
        ghost_suggestion: Optional ghost suggestion from autocomplete
        draft: Optional draft text for micro_tip generation
        lesson_frame: Optional lesson frame for micro_tip generation

    Returns:
        Dict matching DraftFeedbackOut schema
    """
    # Calculate bar score (weighted average)
    bar_score_raw = (
        eval_result["spelling_score"] * 0.20 +
        eval_result["grammar_score"] * 0.25 +
        100 * 0.10 +  # syntax (perfect for now)
        eval_result["lesson_alignment_score"] * 0.30 +
        eval_result["naturalness_score"] * 0.15
    )

    # Map issues to DraftIssue schema
    issues = []
    for issue in eval_result.get("top_issues", []):
        issues.append({
            "category": issue["category"],
            "title": issue["title"],
            "explanation": issue["explanation"],
            "highlight_spans": issue.get("highlight_spans", []),
            "suggestions": issue.get("suggestions", [])
        })

    # Generate micro_tip when no issues
    micro_tip = None
    if not issues and draft:
        micro_tip = _generate_micro_tip(draft, lesson_frame or {})

    return DraftFeedbackOut(
        type="draft_feedback",
        conversation_id=conversation_id,
        bar_score_raw=bar_score_raw,
        bar_score_components={
            "spelling": eval_result["spelling_score"],
            "grammar": eval_result["grammar_score"],
            "syntax": 100.0,
            "lesson_alignment": eval_result["lesson_alignment_score"],
            "naturalness": eval_result["naturalness_score"]
        },
        lesson_alignment_score=eval_result["lesson_alignment_score"],
        issues=issues,
        ghost_suggestion=ghost_suggestion,
        micro_tip=micro_tip,
        server_ts_ms=now_ms
    ).model_dump()


def _sanitize_assistant_response(response: str) -> str:
    """
    Remove extra user simulation from LLM response.

    Defensive post-processing to handle cases where LLM ignores instructions
    and generates a second turn simulating the user's speech.

    Removes:
    1. Quoted paragraph at the end (often looks like user simulation)
    2. Any text after role labels (User:, Student:, etc.)

    Args:
        response: Raw LLM response

    Returns:
        Sanitized response with user simulation removed
    """
    lines = response.split('\n')

    # Remove quoted paragraph at the end (looks like user simulation)
    # Pattern: blank line followed by line starting with quote
    if len(lines) >= 2 and not lines[-2].strip():
        if lines[-1].strip().startswith('"'):
            lines = lines[:-1]

    # Truncate at role labels (LLM started a second turn)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(('User:', 'USER:', 'Student:', 'STUDENT:')):
            lines = lines[:i]
            break

    return '\n'.join(lines).strip()


def _build_context_messages(conversation_id: str, db: Session, limit: int = 10,
                          exclude_system: bool = False) -> List[dict]:
    """
    Build context messages for LLM, ensuring the most recent user message is included.

    Strategy:
    1. Optionally exclude system message (when exclude_system=True)
    2. Fetch the last N non-system messages in descending order
    3. Reverse in memory to get chronological order
    4. Combine: [system] + reversed(last_non_system) or just reversed(last_non_system)

    Args:
        conversation_id: UUID of the conversation
        db: Database session
        limit: Maximum number of non-system messages to include (default: 10)
        exclude_system: If True, exclude system message from context (default: False)

    Returns:
        List of message dicts with 'role' and 'content' keys
    """
    # 1. Get system message (if exists and not excluded)
    system_msg = None
    if not exclude_system:
        system_msg = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.role == "system"
        ).first()

    # 2. Get last N non-system messages in descending order
    last_non_system = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation_id,
        ChatMessage.role != "system"
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()

    # 3. Reverse to get chronological order
    last_non_system.reverse()

    # 4. Build messages list
    messages = []
    if system_msg:
        messages.append({"role": system_msg.role, "content": system_msg.content})

    messages.extend([
        {"role": m.role, "content": m.content}
        for m in last_non_system
    ])

    return messages


# ============================================================================
# REST Endpoints
# ============================================================================

@router.post("/conversations", response_model=ChatConversationResponse)
async def create_conversation(
    conversation_data: ChatConversationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new Chat Coach conversation.

    Creates a conversation with default lesson frame and empty session summary.
    """
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == conversation_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "User not found", "message": f"User '{conversation_data.user_id}' not found"}
            )

        # Create conversation
        conversation = ChatConversation(
            user_id=conversation_data.user_id,
            title=conversation_data.title,
            student_profile_json=get_default_student_profile(),
            lesson_frame_json=get_default_lesson_frame(),
            session_summary=""
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        # Create system message (teacher prompt)
        system_message = ChatMessage(
            conversation_id=conversation.id,
            role="system",
            content=f"You are an English teacher helping a {conversation.lesson_frame_json.get('cefr_target', 'A2')} level student practice conversation."
        )
        db.add(system_message)
        db.commit()

        return ChatConversationResponse(
            id=str(conversation.id),
            user_id=str(conversation.user_id),
            title=conversation.title,
            student_profile_json=conversation.student_profile_json,
            lesson_frame_json=conversation.lesson_frame_json,
            session_summary=conversation.session_summary,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/conversations")
async def list_conversations(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    List all conversations for a user (ordered by updated_at DESC).
    """
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "User not found", "message": f"User '{user_id}' not found"}
            )

        # Get conversations
        conversations = db.query(ChatConversation).filter(
            ChatConversation.user_id == user_id
        ).order_by(ChatConversation.updated_at.desc()).all()

        # Count messages for each conversation
        result = []
        for conv in conversations:
            message_count = db.query(ChatMessage).filter(
                ChatMessage.conversation_id == conv.id
            ).count()

            result.append({
                "id": str(conv.id),
                "user_id": str(conv.user_id),
                "title": conv.title,
                "student_profile_json": conv.student_profile_json,
                "lesson_frame_json": conv.lesson_frame_json,
                "session_summary": conv.session_summary,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "message_count": message_count
            })

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get all messages for a conversation (ordered by created_at ASC).

    Query parameters:
    - limit: max messages to return (default: 100)
    - offset: pagination offset (default: 0)
    """
    try:
        # Verify conversation exists
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Conversation not found", "message": f"Conversation '{conversation_id}' not found"}
            )

        # Get messages
        messages = db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.created_at.asc()).offset(offset).limit(limit).all()

        return [
            ChatMessageResponse(
                id=str(msg.id),
                conversation_id=str(msg.conversation_id),
                role=msg.role,
                content=msg.content,
                metadata_json=msg.metadata_json,
                created_at=msg.created_at
            )
            for msg in messages
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages (CASCADE).
    """
    try:
        # Verify conversation exists
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Conversation not found", "message": f"Conversation '{conversation_id}' not found"}
            )

        # Delete conversation (messages will be CASCADE deleted)
        db.delete(conversation)
        db.commit()

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "message": str(e)}
        )


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws/{conversation_id}")
async def chat_websocket(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for real-time Chat Coach communication.

    Supports events:
    - draft_update → draft_feedback
    - request_autocomplete → draft_feedback (with ghost_suggestion)
    - user_message → assistant_stream_token* → assistant_done
    - ping → pong
    """
    await websocket.accept()

    try:
        # Verify conversation exists
        db = next(get_db())
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()

        if not conversation:
            await websocket.send_json(ErrorOut(
                type="error",
                message="Conversation not found",
                code="NOT_FOUND"
            ).model_dump())
            await websocket.close()
            return

        # Initialize micro_eval timestamp for this conversation if not exists
        if conversation_id not in _micro_eval_timestamps:
            _micro_eval_timestamps[conversation_id] = 0

        # Main WebSocket loop
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            event_type = data.get("type")

            now_ms = int(datetime.now().timestamp() * 1000)

            # Route events by type
            if event_type == "draft_update":
                await handle_draft_update(websocket, data, conversation, now_ms, db)

            elif event_type == "request_autocomplete":
                await handle_request_autocomplete(websocket, data, conversation, db)

            elif event_type == "user_message":
                await handle_user_message(websocket, data, conversation, db)

            elif event_type == "ping":
                await websocket.send_json(Pong(
                    type="pong",
                    ts=data.get("ts", now_ms)
                ).model_dump())

            else:
                await websocket.send_json(ErrorOut(
                    type="error",
                    message=f"Unknown event type: {event_type}",
                    code="UNKNOWN_EVENT"
                ).model_dump())

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: conversation_id={conversation_id}")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json(ErrorOut(
                type="error",
                message=str(e),
                code="INTERNAL_ERROR"
            ).model_dump())
        except:
            pass
    finally:
        if 'db' in locals():
            db.close()


async def handle_draft_update(websocket: WebSocket, data: dict, conversation: ChatConversation, now_ms: int, db: Session):
    """Handle draft_update event → return draft_feedback"""
    draft_text = data.get("draft_text", "")

    # Check throttle for micro_eval (10-15 Hz max)
    last_eval_ts = _micro_eval_timestamps.get(conversation.id, 0)
    should_run_micro_eval = (now_ms - last_eval_ts) >= CHAT_MICRO_EVAL_MIN_INTERVAL_MS

    if should_run_micro_eval:
        # Update timestamp
        _micro_eval_timestamps[conversation.id] = now_ms

        # Run micro_eval (MockLLMProvider)
        eval_result = await llm_provider.micro_eval(
            context=conversation.session_summary,
            lesson_frame=conversation.lesson_frame_json,
            draft=draft_text,
            student_profile=conversation.student_profile_json
        )

        # Build and send draft_feedback using helper (no ghost suggestion)
        feedback = _build_draft_feedback(
            conversation_id=str(conversation.id),
            eval_result=eval_result,
            now_ms=now_ms,
            ghost_suggestion=None,
            draft=draft_text,
            lesson_frame=conversation.lesson_frame_json
        )
        await websocket.send_json(feedback)
    else:
        # Micro_eval throttled: send quick feedback without LLM call
        # For now, just acknowledge (in real implementation, run fast analyzers)
        pass


async def handle_request_autocomplete(websocket: WebSocket, data: dict, conversation: ChatConversation, db: Session):
    """
    Handle request_autocomplete event → return draft_feedback with ghost_suggestion

    CRITICAL FIX: Now runs micro_eval FIRST to get real issues, then adds ghost suggestion.
    This prevents the panel from clearing issues when autocomplete triggers.
    """
    draft_text = data.get("draft_text", "")

    # Step 1: Run micro_eval to get real issues and scores
    eval_result = await llm_provider.micro_eval(
        context=conversation.session_summary,
        lesson_frame=conversation.lesson_frame_json,
        draft=draft_text,
        student_profile=conversation.student_profile_json
    )

    # Step 2: Call autocomplete to get ghost suggestion
    autocomplete_result = await llm_provider.autocomplete(
        context=conversation.session_summary,
        lesson_frame=conversation.lesson_frame_json,
        draft=draft_text,
        student_profile=conversation.student_profile_json
    )

    now_ms = int(datetime.now().timestamp() * 1000)

    # Step 3: Build feedback with REAL issues + ghost suggestion
    feedback = _build_draft_feedback(
        conversation_id=str(conversation.id),
        eval_result=eval_result,
        now_ms=now_ms,
        ghost_suggestion=autocomplete_result.get("ghost_suggestion", ""),
        draft=draft_text,
        lesson_frame=conversation.lesson_frame_json
    )

    # Send draft_feedback with real issues + ghost suggestion
    await websocket.send_json(feedback)


async def handle_user_message(websocket: WebSocket, data: dict, conversation: ChatConversation, db: Session):
    """Handle user_message event → stream assistant response → assistant_done"""
    content = data.get("content", "")

    # Run micro_eval to freeze feedback for the message being sent
    eval_result = await llm_provider.micro_eval(
        context=conversation.session_summary,
        lesson_frame=conversation.lesson_frame_json,
        draft=content,
        student_profile=conversation.student_profile_json
    )

    # Send draft_feedback to freeze the feedback (without ghost suggestion)
    now_ms = int(datetime.now().timestamp() * 1000)
    feedback = _build_draft_feedback(
        conversation_id=str(conversation.id),
        eval_result=eval_result,
        now_ms=now_ms,
        ghost_suggestion=None,
        draft=content,
        lesson_frame=conversation.lesson_frame_json
    )
    await websocket.send_json(feedback)

    # Persist user message
    user_message = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=content
    )
    db.add(user_message)
    db.commit()

    # Build messages for LLM excluding system (we'll inject fresh system_prompt)
    messages = _build_context_messages(str(conversation.id), db, limit=10, exclude_system=True)

    # Build system prompt from lesson_frame
    lesson_frame = conversation.lesson_frame_json
    system_prompt = f"""You are an English conversation tutor helping a {lesson_frame.get('cefr_target', 'A2')} level student.

Learning Goal: {lesson_frame.get('learning_goal', 'conversation practice')}
Topic: {lesson_frame.get('topic', 'general conversation')}
Expected Intent: {lesson_frame.get('expected_intent', 'general conversation')}

CRITICAL INSTRUCTIONS:
- Reply as the assistant ONLY.
- Never write the student's next message or simulate their speech.
- Do not include quoted example replies.
- No role labels like "User:", "Assistant:", "Student:".
- Answer naturally and briefly in 1-3 sentences.
- Always ask one relevant follow-up question to keep the conversation going.
- If the user writes in Portuguese/Spanish, gently encourage them to switch to English.
- Do NOT continue the conversation by writing what the user might say next.
"""
    full_response = ""

    # Generation config (standard LLM params only, no internal objects)
    generation_config = {
        "temperature": 0.5,
        "max_tokens": 300,
        "top_p": 0.9,
        "stop": ['\n"', '\nUser:', '\nUSER:', '\nStudent:', '\nSTUDENT:', '', ''],
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }

    async for token in llm_provider.chat_stream(messages, system_prompt, generation_config):
        full_response += token
        await websocket.send_json(AssistantStreamTokenOut(
            type="assistant_stream_token",
            conversation_id=str(conversation.id),
            token=token
        ).model_dump())

    # Defensive sanitization to remove any user simulation LLM may have generated
    full_response = _sanitize_assistant_response(full_response)

    # Persist assistant message
    assistant_message = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=full_response
    )
    db.add(assistant_message)

    # Update conversation (lesson_frame, session_summary)
    # For now, keep the same lesson_frame (in real implementation, LLM would generate new one)
    conversation.updated_at = datetime.utcnow()
    db.commit()

    # Send assistant_done
    await websocket.send_json(AssistantDoneOut(
        type="assistant_done",
        conversation_id=str(conversation.id),
        full_content=full_response,
        lesson_frame=conversation.lesson_frame_json,
        summary_update="Student sent a message."
    ).model_dump())
