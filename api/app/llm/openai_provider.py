"""OpenAI LLM Provider via HTTP (no SDK)"""

import logging
from typing import AsyncGenerator, Dict, Any, List
import httpx

from app.llm.provider_base import LLMProvider
from app.llm.mock_provider import MockLLMProvider

logger = logging.getLogger(__name__)


class OpenAILLMProvider(LLMProvider):
    """
    OpenAI API provider using HTTP (no SDK).

    Features:
    - chat_stream: Real OpenAI responses
    - micro_eval: Delegates to MockLLMProvider for now
    - autocomplete: Delegates to MockLLMProvider for now
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

    async def micro_eval(
        self,
        context: str,
        lesson_frame: Dict[str, Any],
        draft: str,
        student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate draft (delegates to MockLLMProvider for now).

        Real LLM-based evaluation is not implemented in this change.
        """
        logger.debug("micro_eval: delegating to MockLLMProvider")
        return await self._mock.micro_eval(context, lesson_frame, draft, student_profile)

    async def autocomplete(
        self,
        context: str,
        lesson_frame: Dict[str, Any],
        draft: str,
        student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate autocomplete (delegates to MockLLMProvider for now).

        Real LLM-based autocomplete is not implemented in this change.
        """
        logger.debug("autocomplete: delegating to MockLLMProvider")
        return await self._mock.autocomplete(context, lesson_frame, draft, student_profile)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
