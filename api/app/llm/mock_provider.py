"""Thin mock LLM provider wrapper for development and testing."""

from typing import Any, AsyncGenerator, Dict, List

from app.llm.mock_chat_responses import (
    _generate_command_response as _generate_command_response_helper,
    _generate_greeting_response as _generate_greeting_response_helper,
    _generate_meta_help_response as _generate_meta_help_response_helper,
    _generate_question_response as _generate_question_response_helper,
    _generate_statement_response as _generate_statement_response_helper,
    chat_stream as _chat_stream_helper,
)
from app.llm.mock_feedback_payloads import (
    autocomplete as _autocomplete_helper,
    generate_teacher_analysis as _generate_teacher_analysis_helper,
    micro_eval as _micro_eval_helper,
)
from app.llm.mock_text_analysis import (
    IRREGULAR_VERBS,
    STOPWORDS,
    _analyze_text as _analyze_text_helper,
)
from app.llm.provider_base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock provider with behavior delegated to extracted helpers."""

    STOPWORDS = STOPWORDS
    IRREGULAR_VERBS = IRREGULAR_VERBS

    def __init__(self):
        """Initialize mock provider."""
        pass

    def _analyze_text(self, text: str, lesson_frame: dict) -> dict:
        return _analyze_text_helper(text, lesson_frame)

    def _generate_greeting_response(self, text: str, analysis: dict) -> str:
        return _generate_greeting_response_helper(text, analysis)

    def _generate_meta_help_response(self, text: str, analysis: dict) -> str:
        return _generate_meta_help_response_helper(text, analysis)

    def _generate_question_response(self, text: str, analysis: dict) -> str:
        return _generate_question_response_helper(text, analysis)

    def _generate_command_response(self, text: str, analysis: dict) -> str:
        return _generate_command_response_helper(text, analysis)

    def _generate_statement_response(self, text: str, analysis: dict) -> str:
        return _generate_statement_response_helper(text, analysis)

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        generation_config: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        async for token in _chat_stream_helper(messages, system_prompt, generation_config):
            yield token

    async def micro_eval(
        self,
        context: str,
        lesson_frame: Dict[str, Any],
        draft: str,
        student_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        return await _micro_eval_helper(context, lesson_frame, draft, student_profile)

    async def autocomplete(
        self,
        context: str,
        lesson_frame: Dict[str, Any],
        draft: str,
        student_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        return await _autocomplete_helper(context, lesson_frame, draft, student_profile)

    async def generate_teacher_analysis(
        self,
        user_message: str,
        context: str,
        lesson_frame: Dict[str, Any],
    ) -> Dict[str, Any]:
        return await _generate_teacher_analysis_helper(user_message, context, lesson_frame)
