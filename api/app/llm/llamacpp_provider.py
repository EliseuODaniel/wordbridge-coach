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

    async def generate_teacher_analysis(
        self,
        user_message: str,
        context: str,
        lesson_frame: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate teacher analysis as JSON (non-streaming, robust parser).

        PASSO 1:
        - Uses stream=False for complete JSON response
        - Prompt: "RETURN JSON ONLY. NO markdown. NO extra text."
        - Robust parser: removes code fences, extracts JSON
        - Fallback with error reason if parsing fails

        Returns structured analysis with:
        - rewrite: Corrected version of user's message
        - corrections: List of {mistake, fix, why}
        - teacher_summary: Brief pedagogical feedback
        - next_practice: 2-3 suggested practice sentences
        """
        # Build teacher-only context (user messages only)
        # PASSO 3: Contextos independentes
        teacher_system_prompt = f"""You are an expert English teacher. Analyze the student's message and return JSON ONLY.

**CRITICAL: RETURN JSON ONLY**
- NO markdown
- NO code blocks (no ```json)
- NO extra text
- ONLY raw JSON

Example format:
{{
  "rewrite": "I enjoyed sleeping.",
  "corrections": [
    {{
      "mistake": "enjoyed to sleep",
      "fix": "enjoyed sleeping",
      "why": "After 'enjoy', use gerund (-ing), not infinitive."
    }}
  ],
  "teacher_summary": "Good attempt! Remember: enjoy + gerund.",
  "next_practice": [
    "I enjoy reading books.",
    "She enjoys playing tennis."
  ]
}}

Student message: "{user_message}"

Return JSON NOW:"""

        try:
            # PASSO 1: Non-streaming call for complete JSON
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": teacher_system_prompt}],
                "stream": False,  # CRITICAL: Non-streaming for JSON
                "temperature": 0.3,  # Lower temperature for consistent JSON
                "max_tokens": 500
            }

            url = f"{self.base_url}/chat/completions"

            logger.info(f"[TEACHER_LLM] Calling llama.cpp for teacher analysis (non-streaming)")

            async with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()

                # Parse response (non-streaming)
                import json
                response_data = json.loads(await response.aread())

                # Extract content from OpenAI-compatible response
                raw_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

                logger.info(f"[TEACHER_LLM] Raw output (first 500 chars): {raw_text[:500]}")

                # PASSO 1: Robust JSON parser
                parsed_analysis = self._parse_teacher_json(raw_text)

                logger.info(f"[TEACHER_LLM] Successfully parsed teacher analysis")
                return parsed_analysis

        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.error(f"[TEACHER_LLM] llama.cpp error: {e}")
            if self.strict:
                raise

            # Fallback to Mock provider
            logger.info(f"[TEACHER_LLM] Falling back to Mock provider")
            return await self._mock.generate_teacher_analysis(user_message, context, lesson_frame)

        except Exception as e:
            logger.exception(f"[TEACHER_LLM] Unexpected error: {e}")
            # PASSO 1: NUNCA retorne "temporarily unavailable" silencioso
            # Retorne com debug_reason
            return {
                "rewrite": None,
                "corrections": [],
                "teacher_summary": f"Teacher analysis error: {str(e)[:100]}",
                "next_practice": [],
                "debug_reason": str(e)[:200]
            }

    def _parse_teacher_json(self, raw_text: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response with robust error handling.

        PASSO 1: Parser robusto
        - Remove code fences (```json, ```)
        - Extract substring from first "{" to last "}"
        - Try json.loads
        - If fail, return Mock analysis

        Args:
            raw_text: Raw text from LLM

        Returns:
            Parsed teacher analysis dict
        """
        import json
        import re

        try:
            # Step 1: Remove code fences if present
            cleaned = raw_text.strip()

            # Remove ```json and ``` markers
            cleaned = re.sub(r'^```json\s*', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'^```\s*', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.IGNORECASE)

            # Step 2: Extract JSON from first { to last }
            first_brace = cleaned.find('{')
            last_brace = cleaned.rfind('}')

            if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
                logger.warning(f"[TEACHER_PARSE] No valid JSON braces found in: {raw_text[:200]}")
                raise ValueError("No valid JSON object found")

            json_str = cleaned[first_brace:last_brace + 1]

            # Step 3: Parse JSON
            parsed = json.loads(json_str)

            # Validate required keys
            required_keys = ["rewrite", "corrections", "teacher_summary", "next_practice"]
            missing_keys = [k for k in required_keys if k not in parsed]

            if missing_keys:
                logger.warning(f"[TEACHER_PARSE] Missing keys: {missing_keys}, adding defaults")
                for key in missing_keys:
                    if key == "rewrite":
                        parsed[key] = None
                    elif key == "corrections":
                        parsed[key] = []
                    elif key == "teacher_summary":
                        parsed[key] = "Analysis incomplete."
                    elif key == "next_practice":
                        parsed[key] = []

            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"[TEACHER_PARSE] JSON decode error: {e} in: {raw_text[:300]}")
            # Return Mock fallback instead of crashing
            return self._mock._analyze_text(raw_text, lesson_frame={})
        except Exception as e:
            logger.error(f"[TEACHER_PARSE] Parse error: {e}")
            # Return Mock fallback
            return self._mock._analyze_text(raw_text, lesson_frame={})

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
