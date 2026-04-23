"""OpenAI LLM Provider via HTTP (no SDK)"""

import json
import logging
from typing import AsyncGenerator, Dict, Any, List
import httpx

from app.llm.pedagogical_tasks import (
    AutocompletePayload,
    DraftEvaluationPayload,
    TeacherAnalysisPayload,
    build_autocomplete_messages,
    build_micro_eval_messages,
    build_openai_response_format,
    build_teacher_analysis_messages,
)
from app.llm.provider_base import LLMProvider
from app.llm.mock_provider import MockLLMProvider

logger = logging.getLogger(__name__)


class OpenAILLMProvider(LLMProvider):
    """
    OpenAI API provider using HTTP (no SDK).

    Features:
    - chat_stream: Real OpenAI responses
    - micro_eval: Structured pedagogical evaluation with mock fallback
    - autocomplete: Structured continuation with mock fallback
    - teacher analysis: Structured post-turn review with mock fallback
    - Automatic fallback to Mock on error
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: int = 30,
        fallback_to_mock: bool = True
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (sk-...)
            model: Model name (gpt-4o-mini, gpt-4o, gpt-3.5-turbo)
            timeout: Request timeout in seconds
            fallback_to_mock: If True, fallback to Mock on error
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.fallback_to_mock = fallback_to_mock

        # Create HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

        # Fallback Mock provider (for micro_eval, autocomplete, errors)
        self._mock = MockLLMProvider()

        # Track if we've fallen back
        self._has_fallen_back = False

    async def _call_openai_chat(
        self,
        messages: List[Dict[str, str]],
        generation_config: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Call OpenAI Chat Completions API and stream tokens.

        Args:
            messages: Conversation history
            generation_config: Generation parameters

        Yields:
            Tokens from OpenAI API

        Raises:
            httpx.HTTPError: On network or API error
        """
        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            **generation_config
        }

        # Make streaming request
        async with self.client.stream(
            "POST",
            "https://api.openai.com/v1/chat/completions",
            json=payload
        ) as response:
            response.raise_for_status()

            # Stream SSE (Server-Sent Events)
            async for line in response.aiter_lines():
                if not line.strip():
                    continue

                if not line.startswith("data: "):
                    continue

                data = line[6:]  # Remove "data: " prefix

                # Skip [DONE] sentinel
                if data.strip() == "[DONE]":
                    break

                # Parse JSON
                try:
                    import json
                    chunk = json.loads(data)

                    # Extract delta content
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    token = delta.get("content", "")

                    if token:
                        yield token

                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse SSE chunk: {data}")
                    continue

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        generation_config: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion from OpenAI.

        Args:
            messages: List of {role, content} dicts
            system_prompt: System prompt (appended to messages if not present)
            generation_config: Generation params (temperature, max_tokens, etc.)

        Yields:
            Tokens from OpenAI API

        Falls back to MockLLMProvider on error if fallback_to_mock=True
        """
        # Ensure system prompt is in messages
        has_system = any(msg.get("role") == "system" for msg in messages)
        if not has_system and system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        # Try OpenAI API
        try:
            async for token in self._call_openai_chat(messages, generation_config):
                yield token

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            if not self.fallback_to_mock:
                logger.error(f"OpenAI API error (no fallback): {e}")
                raise

            if not self._has_fallen_back:
                logger.warning(f"OpenAI API error, falling back to Mock: {e}")
                self._has_fallen_back = True

            # Fallback to Mock
            async for token in self._mock.chat_stream(messages, system_prompt, generation_config):
                yield token

        except Exception as e:
            logger.exception(f"Unexpected error in OpenAI provider: {e}")
            # Always fallback on unexpected errors
            if self.fallback_to_mock:
                async for token in self._mock.chat_stream(messages, system_prompt, generation_config):
                    yield token
            else:
                raise

    async def _request_structured_output(
        self,
        *,
        messages: List[Dict[str, str]],
        response_model,
        schema_name: str,
        temperature: float,
        max_tokens: int,
    ) -> dict:
        """Request structured JSON from OpenAI and validate it locally."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": build_openai_response_format(schema_name, response_model),
        }
        response = await self.client.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
        )
        response.raise_for_status()

        response_data = response.json()
        content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("OpenAI returned empty structured content")

        return response_model.model_validate(json.loads(content)).model_dump()

    async def micro_eval(
        self,
        context: str,
        lesson_frame: Dict[str, Any],
        draft: str,
        student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a learner draft with structured pedagogical feedback.
        """
        try:
            return await self._request_structured_output(
                messages=build_micro_eval_messages(
                    context=context,
                    lesson_frame=lesson_frame,
                    draft=draft,
                    student_profile=student_profile,
                ),
                response_model=DraftEvaluationPayload,
                schema_name="draft_evaluation",
                temperature=0.1,
                max_tokens=700,
            )
        except Exception as error:
            logger.warning("OpenAI micro_eval failed, falling back to Mock: %s", error)
            if self.fallback_to_mock:
                return await self._mock.micro_eval(context, lesson_frame, draft, student_profile)
            raise

    async def autocomplete(
        self,
        context: str,
        lesson_frame: Dict[str, Any],
        draft: str,
        student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a short structured ghost suggestion.
        """
        try:
            return await self._request_structured_output(
                messages=build_autocomplete_messages(
                    context=context,
                    lesson_frame=lesson_frame,
                    draft=draft,
                    student_profile=student_profile,
                ),
                response_model=AutocompletePayload,
                schema_name="autocomplete_hint",
                temperature=0.1,
                max_tokens=120,
            )
        except Exception as error:
            logger.warning("OpenAI autocomplete failed, falling back to Mock: %s", error)
            if self.fallback_to_mock:
                return await self._mock.autocomplete(context, lesson_frame, draft, student_profile)
            raise

    async def generate_teacher_analysis(
        self,
        user_message: str,
        context: str,
        lesson_frame: Dict[str, Any],
        student_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate structured post-turn teacher analysis."""
        try:
            return await self._request_structured_output(
                messages=build_teacher_analysis_messages(
                    user_message=user_message,
                    context=context,
                    lesson_frame=lesson_frame,
                    student_profile=student_profile,
                ),
                response_model=TeacherAnalysisPayload,
                schema_name="teacher_analysis",
                temperature=0.2,
                max_tokens=900,
            )
        except Exception as error:
            logger.warning("OpenAI teacher analysis failed, falling back to Mock: %s", error)
            if self.fallback_to_mock:
                fallback = await self._mock.generate_teacher_analysis(
                    user_message,
                    context,
                    lesson_frame,
                    student_profile,
                )
                return {
                    **fallback,
                    "debug_reason": str(error)[:200],
                }
            raise

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
