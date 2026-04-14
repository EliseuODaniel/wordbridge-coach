"""Streaming and teacher-analysis generation helpers for Chat Coach."""

from __future__ import annotations

import logging

from app.schemas.chat import AssistantStreamTokenOut

logger = logging.getLogger(__name__)


async def stream_assistant_response(
    websocket,
    conversation_id: str,
    chat_provider,
    messages,
    system_prompt: str,
    generation_config: dict,
) -> str:
    """Stream assistant tokens to the websocket and return the aggregated text."""
    full_response = ""

    logger.info(
        "[CHAT_LLM] Starting stream with profile chat_provider.model=%s",
        chat_provider.model,
    )
    async for token in chat_provider.chat_stream(messages, system_prompt, generation_config):
        full_response += token
        await websocket.send_json(
            AssistantStreamTokenOut(
                type="assistant_stream_token",
                conversation_id=conversation_id,
                token=token,
            ).model_dump()
        )

    return full_response


async def generate_teacher_analysis_with_fallback(
    teacher_provider,
    conversation,
    teacher_context: str,
    content: str,
    build_fallback,
) -> tuple[dict, bool]:
    """Generate teacher analysis and fall back to a safe payload on failure."""
    conv_id_str = str(conversation.id)

    try:
        logger.info(
            "[TEACHER_ANALYSIS] Starting generation for conv=%s with profile teacher_provider.model=%s",
            conv_id_str[:8],
            teacher_provider.model,
        )

        teacher_analysis = await teacher_provider.generate_teacher_analysis(
            user_message=content,
            context=teacher_context,
            lesson_frame=conversation.lesson_frame_json,
        )

        logger.info(
            "[TEACHER_ANALYSIS] Generated successfully, keys=%s",
            list(teacher_analysis.keys()) if teacher_analysis else "None",
        )
        return teacher_analysis, False
    except Exception as error:
        logger.error("[TEACHER_ANALYSIS] Failed to generate: %s", error)
        return build_fallback(error), True
