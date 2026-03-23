"""Base LLM Provider interface for Chat Coach mode"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List


class LLMProvider(ABC):
    """
    Abstract interface for LLM providers (pluggable architecture).

    Supported providers:
    - MockLLMProvider (development, no GPU)
    - LlamaCppProvider (production, local llama.cpp server)
    - OpenAIProvider (optional, cloud API)
    """

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        generation_config: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion token by token.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: System prompt for the assistant
            generation_config: Generation parameters (temperature, max_tokens, etc.)

        Yields:
            Tokens (strings) as they are generated
        """
        pass

    @abstractmethod
    async def micro_eval(
        self,
        context: str,
        lesson_frame: Dict[str, Any],
        draft: str,
        student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate draft against lesson frame and return scores + issues.

        Args:
            context: Recent conversation context
            lesson_frame: Current pedagogical objective
            draft: Student's draft text
            student_profile: Student's CEFR level and common errors

        Returns:
            Dict with:
            - grammar_score (0-100)
            - spelling_score (0-100)
            - naturalness_score (0-100)
            - lesson_alignment_score (0-100)
            - top_issues (list of issue dicts)
            - suggested_next_words (list of strings)
            - micro_tip (short helpful sentence)
        """
        pass

    @abstractmethod
    async def autocomplete(
        self,
        context: str,
        lesson_frame: Dict[str, Any],
        draft: str,
        student_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate short ghost suggestion (1-6 words) for autocomplete.

        Args:
            context: Recent conversation context
            lesson_frame: Current pedagogical objective
            draft: Student's draft text
            student_profile: Student's CEFR level and common errors

        Returns:
            Dict with:
            - ghost_suggestion (1-6 words)
            - reason (brief explanation)
        """
        pass
