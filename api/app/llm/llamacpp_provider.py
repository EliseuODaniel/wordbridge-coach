"""llama.cpp LLM Provider (OpenAI-compatible HTTP)"""

import json
import logging
from typing import AsyncGenerator, Dict, Any, List
import httpx

from app.llm.pedagogical_tasks import (
    AutocompletePayload,
    DraftEvaluationPayload,
    TeacherAnalysisPayload,
    build_autocomplete_messages,
    build_llamacpp_response_format,
    build_micro_eval_messages,
    build_teacher_analysis_messages,
)
from app.llm.provider_base import LLMProvider
from app.llm.mock_provider import MockLLMProvider

logger = logging.getLogger(__name__)


# Supported generation parameters (OpenAI-compatible)
SUPPORTED_PARAMS = {
    "temperature",
    "max_tokens",
    "top_p",
    "frequency_penalty",
    "presence_penalty",
    "stop",
    "stream"
}


class LlamaCppLLMProvider(LLMProvider):
    """
    llama.cpp server provider (OpenAI-compatible API).

    Features:
    - chat_stream: Real LLM responses via llama.cpp
    - micro_eval: Structured pedagogical evaluation with mock fallback
    - autocomplete: Structured short continuation with mock fallback
    - teacher analysis: Structured post-turn review with mock fallback
    - Optional strict mode (raise instead of fallback for chat streaming)
    - No API key required
    """

    def __init__(
        self,
        base_url: str,
        model: str = "gemma-4-e4b-it",
        timeout: int = 60,
        strict: bool = False
    ):
        """
        Initialize llama.cpp provider.

        Args:
            base_url: Base URL with /v1 suffix (e.g., http://llm:8080/v1)
            model: Model name (filename without .gguf)
            timeout: Request timeout in seconds
            strict: If True, raise on error instead of falling back to Mock
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.strict = strict

        # Create HTTP client with timeout (no API key)
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Content-Type": "application/json"
            }
        )

        # Fallback Mock provider (for micro_eval, autocomplete, errors)
        self._mock = MockLLMProvider()

        # Track if we've fallen back
        self._has_fallen_back = False

    def _filter_generation_config(self, generation_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter generation_config to only include supported parameters.

        Removes internal params like 'lesson_frame' that llama.cpp doesn't understand.
        Filters empty strings from 'stop' parameter (empty strings cause LLM to generate 0 tokens).

        Args:
            generation_config: Full generation config

        Returns:
            Filtered config with only supported params
        """
        filtered = {}
        for key, value in generation_config.items():
            if key not in SUPPORTED_PARAMS:
                # Log that we're filtering this param
                logger.debug(f"Filtering unsupported param: {key}")
                continue

            # Special handling for 'stop' parameter
            if key == "stop":
                if isinstance(value, list):
                    # Filter out empty/whitespace strings
                    filtered_stop = [s for s in value if isinstance(s, str) and s.strip()]
                    if filtered_stop:
                        filtered[key] = filtered_stop
                    else:
                        logger.debug("Filtering empty stop list")
                elif isinstance(value, str):
                    # Single stop string - only include if non-empty
                    if value.strip():
                        filtered[key] = value
                    else:
                        logger.debug("Filtering empty stop string")
                # else: ignore other types
            else:
                filtered[key] = value

        return filtered

    async def _call_llamacpp_chat(
        self,
        messages: List[Dict[str, str]],
        generation_config: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Call llama.cpp server (OpenAI-compatible) and stream tokens.

        Args:
            messages: Conversation history
            generation_config: Generation parameters (will be filtered)

        Yields:
            Tokens from llama.cpp server

        Raises:
            httpx.HTTPError: On network or API error
        """
        # Filter generation config
        filtered_config = self._filter_generation_config(generation_config)

        # Prepare request payload (OpenAI-compatible)
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            **filtered_config
        }

        # Construct endpoint URL
        url = f"{self.base_url}/chat/completions"

        logger.debug(f"Calling llama.cpp at {url} with model {self.model}")

        # Make streaming request
        async with self.client.stream(
            "POST",
            url,
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

                    # Extract delta content (OpenAI-compatible format)
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
        Stream chat completion from llama.cpp.

        Args:
            messages: List of {role, content} dicts
            system_prompt: System prompt (appended to messages if not present)
            generation_config: Generation params (temperature, max_tokens, etc.)

        Yields:
            Tokens from llama.cpp server

        Falls back to MockLLMProvider on error if strict=False
        """
        # Ensure system prompt is in messages
        has_system = any(msg.get("role") == "system" for msg in messages)
        if not has_system and system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        # Try llama.cpp server
        try:
            async for token in self._call_llamacpp_chat(messages, generation_config):
                yield token

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            if self.strict:
                logger.error(f"llama.cpp error (strict mode, no fallback): {e}")
                raise

            if not self._has_fallen_back:
                logger.warning(f"llama.cpp error, falling back to Mock: {e}")
                self._has_fallen_back = True

            # Fallback to Mock
            async for token in self._mock.chat_stream(messages, system_prompt, generation_config):
                yield token

        except Exception as e:
            logger.exception(f"Unexpected error in llama.cpp provider: {e}")
            # Always fallback on unexpected errors (unless strict)
            if self.strict:
                raise
            else:
                async for token in self._mock.chat_stream(messages, system_prompt, generation_config):
                    yield token

    async def _request_structured_output(
        self,
        *,
        messages: List[Dict[str, str]],
        response_model,
        temperature: float,
        max_tokens: int,
    ) -> dict:
        """Request schema-constrained JSON from llama.cpp and validate it."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": build_llamacpp_response_format(response_model),
        }
        url = f"{self.base_url}/chat/completions"
        response = await self.client.post(url, json=payload)
        response.raise_for_status()

        response_data = response.json()
        content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            content = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
            )

        if not isinstance(content, str) or not content.strip():
            raise ValueError("llama.cpp returned empty structured content")

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
                temperature=0.1,
                max_tokens=700,
            )
        except Exception as error:
            logger.warning("micro_eval structured output failed, falling back to Mock: %s", error)
            return await self._mock.micro_eval(context, lesson_frame, draft, student_profile)

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
                temperature=0.1,
                max_tokens=120,
            )
        except Exception as error:
            logger.warning("autocomplete structured output failed, falling back to Mock: %s", error)
            return await self._mock.autocomplete(context, lesson_frame, draft, student_profile)

    async def generate_teacher_analysis(
        self,
        user_message: str,
        context: str,
        lesson_frame: Dict[str, Any],
        student_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate structured post-turn teacher analysis.
        """
        try:
            return await self._request_structured_output(
                messages=build_teacher_analysis_messages(
                    user_message=user_message,
                    context=context,
                    lesson_frame=lesson_frame,
                    student_profile=student_profile,
                ),
                response_model=TeacherAnalysisPayload,
                temperature=0.2,
                max_tokens=900,
            )
        except Exception as error:
            logger.warning(
                "teacher analysis structured output failed, falling back to Mock: %s",
                error,
            )
            if self.strict and isinstance(error, (httpx.HTTPError, httpx.TimeoutException)):
                raise

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

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
