"""llama.cpp LLM Provider (OpenAI-compatible HTTP)"""

import logging
from typing import AsyncGenerator, Dict, Any, List
import httpx

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
    - micro_eval: Heuristic-based (delegates to Mock)
    - autocomplete: Heuristic-based (delegates to Mock)
    - Optional strict mode (raise instead of fallback)
    - No API key required
    """

    def __init__(
        self,
        base_url: str,
        model: str = "qwen2.5-7b-instruct",
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

        Args:
            generation_config: Full generation config

        Returns:
            Filtered config with only supported params
        """
        filtered = {}
        for key, value in generation_config.items():
            if key in SUPPORTED_PARAMS:
                filtered[key] = value
            else:
                # Log that we're filtering this param
                logger.debug(f"Filtering unsupported param: {key}")

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

    async def micro_eval(
        self,
        context: str,
        lesson_frame: Dict[str, Any],
        draft: str,
        student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate draft using heuristic analysis.

        Real LLM-based evaluation not implemented yet.
        Delegates to MockLLMProvider heuristic logic.
        """
        logger.debug("micro_eval: using heuristic analysis (Mock)")
        return await self._mock.micro_eval(context, lesson_frame, draft, student_profile)

    async def autocomplete(
        self,
        context: str,
        lesson_frame: Dict[str, Any],
        draft: str,
        student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate autocomplete using heuristic analysis.

        Real LLM-based autocomplete not implemented yet.
        Delegates to MockLLMProvider heuristic logic.
        """
        logger.debug("autocomplete: using heuristic analysis (Mock)")
        return await self._mock.autocomplete(context, lesson_frame, draft, student_profile)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
