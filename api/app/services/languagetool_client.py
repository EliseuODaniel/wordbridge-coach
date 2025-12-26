"""LanguageTool Client

Real-time grammar and spell checking using LanguageTool HTTP API.
Converts LanguageTool matches to DraftIssue format.
"""

import logging
from typing import Dict, List, Any, Optional
import os
import httpx

logger = logging.getLogger(__name__)

# LanguageTool rule category → our category mapping
LT_CATEGORY_MAP = {
    'GRAMMAR': 'grammar',
    'SPELLING': 'spelling',
    'STYLE': 'style',
    'TYPOGRAPHY': 'style',
    'CASING': 'grammar',  # e.g., "capitalize first letter"
    'PUNCTUATION': 'grammar',
    'OTHER': 'style'
}


class LanguageToolClient:
    """Client for LanguageTool HTTP API."""

    def __init__(
        self,
        base_url: str = None,
        language: str = 'en-US',
        timeout: float = 5.0
    ):
        """
        Initialize LanguageTool client.

        Args:
            base_url: LanguageTool base URL (default from env or localhost:8010)
            language: Language code (default: en-US)
            timeout: Request timeout in seconds
        """
        self.base_url = (base_url or os.getenv('CHAT_LANGUAGETOOL_URL', 'http://localhost:8010')).rstrip('/')
        self.language = language
        self.timeout = timeout

        # Create HTTP client
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout)
        )

    def _lt_category_to_our_category(self, lt_category: str) -> str:
        """Map LanguageTool category to our category."""
        # Handle both string and dict (in case API structure changes)
        if isinstance(lt_category, dict):
            lt_category = lt_category.get('name', 'OTHER')
        elif not isinstance(lt_category, str):
            lt_category = str(lt_category)

        return LT_CATEGORY_MAP.get(lt_category.upper() if lt_category else 'OTHER', 'style')

    def _match_to_issue(
        self,
        match: Dict[str, Any],
        text: str
    ) -> Dict[str, Any]:
        """
        Convert LanguageTool match to DraftIssue format.

        Args:
            match: LanguageTool match object
            text: Original text (for validation)

        Returns:
            DraftIssue dict
        """
        rule = match.get('rule', {})
        rule_category = rule.get('category', 'OTHER')

        # Map category
        category = self._lt_category_to_our_category(rule_category)

        # Extract positions
        offset = match.get('offset', 0)
        length = match.get('length', 0)

        # Validate positions
        if offset < 0 or offset >= len(text):
            logger.warning(f"Invalid offset {offset} for text length {len(text)}")
            offset = max(0, min(offset, len(text) - 1))

        if offset + length > len(text):
            logger.warning(f"Invalid length {length} at offset {offset} for text length {len(text)}")
            length = max(1, len(text) - offset)

        # Extract suggestions (replacements)
        replacements = match.get('replacements', [])
        suggestions = [r.get('value', '') for r in replacements[:5]]  # Top 5

        # Build issue
        issue = {
            'category': category,
            'title': match.get('message', rule.get('id', 'Error detected')),
            'explanation': match.get('shortMessage', ''),
            'highlight_spans': [
                {
                    'start': offset,
                    'end': offset + length
                }
            ],
            'suggestions': suggestions
        }

        return issue

    async def check_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Check text for grammar and spelling errors.

        Args:
            text: Text to check

        Returns:
            List of DraftIssue dicts

        Raises:
            httpx.HTTPError: On network or API error
        """
        if not text or not text.strip():
            return []

        # Prepare request
        url = f"{self.base_url}/v2/check"
        params = {'language': self.language}
        form_data = {'text': text, 'enabledOnly': 'false'}

        try:
            # Call LanguageTool
            logger.debug(f"Checking text ({len(text)} chars) with LanguageTool")
            response = await self.client.post(url, params=params, data=form_data)
            response.raise_for_status()

            # Parse response
            result = response.json()
            matches = result.get('matches', [])

            logger.debug(f"LanguageTool returned {len(matches)} matches")

            # Convert matches to issues
            issues = []
            for match in matches:
                try:
                    issue = self._match_to_issue(match, text)
                    issues.append(issue)
                except Exception as e:
                    logger.warning(f"Failed to convert match to issue: {e}")
                    continue

            return issues

        except httpx.HTTPError as e:
            logger.error(f"LanguageTool API error: {e}")
            raise

        except Exception as e:
            logger.exception(f"Unexpected error in LanguageTool check: {e}")
            return []

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
