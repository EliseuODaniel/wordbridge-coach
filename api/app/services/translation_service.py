"""Translation service for Lingvist mode.

Supports multiple providers:
- Argos Translate (offline MT, requires local models)
- Google Translate HTTP API (network required, no extra deps)

Translations are cached in database to avoid re-translation.
"""

import logging
import httpx
from typing import Optional
from decouple import config
from urllib.parse import quote

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translating text using multiple providers."""

    def __init__(self):
        # Configuration
        self._enabled = config("LINGVIST_TRANSLATIONS_AUTOFILL", default=False, cast=bool)
        self._provider = config("LINGVIST_TRANSLATIONS_PROVIDER", default="google_http")
        self._network_enabled = config("LINGVIST_TRANSLATIONS_NETWORK_ENABLED", default=False, cast=bool)
        self._target_lang = config("LINGVIST_TRANSLATIONS_TARGET_LANG", default="pt")
        self._timeout_s = config("LINGVIST_TRANSLATIONS_TIMEOUT_S", default=6, cast=int)

        # Argos Translate state
        self._argos_translator = None
        self._argos_initialized = False

    def _ensure_argos_initialized(self):
        """Lazy initialization of Argos Translate (downloads models on first use)."""
        if self._argos_initialized or self._provider != "argos":
            return

        try:
            import argostranslate.package
            import argostranslate.translate

            # Download and install English→Portuguese translation package
            logger.info("Initializing Argos Translate: downloading EN→PT model...")

            # Update package index
            argostranslate.package.update_package_index()

            # Get available packages
            available_packages = argostranslate.package.get_available_packages()
            en_to_pt_packages = [
                pkg for pkg in available_packages
                if pkg.from_code == "en" and pkg.to_code == self._target_lang
            ]

            if not en_to_pt_packages:
                logger.error(f"EN→{self._target_lang} translation package not found in Argos Translate")
                return

            # Download first available package
            en_to_pt_package = en_to_pt_packages[0]
            logger.info(f"Downloading package: {en_to_pt_package.package_version}")
            argostranslate.package.install_from_path(en_to_pt_package.download())

            # Create translator
            self._argos_translator = argostranslate.translate.get_translation_from_code(
                "en", self._target_lang
            )

            self._argos_initialized = True
            logger.info("✅ Argos Translate initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Argos Translate: {e}")
            # Don't disable entire service, just Argos
            logger.warning("Argos Translate unavailable, will use other providers if configured")

    def _translate_with_argos(self, text: str) -> Optional[str]:
        """Translate using Argos Translate (offline)."""
        try:
            self._ensure_argos_initialized()

            if not self._argos_translator:
                logger.warning("Argos Translate not initialized")
                return None

            # Translate
            translated = self._argos_translator.translate(text.strip())
            logger.debug(f"Argos: '{text[:50]}...' → '{translated[:50]}...'")
            return translated

        except Exception as e:
            logger.error(f"Argos Translate failed for '{text[:50]}...': {e}")
            return None

    def _translate_with_google_http(self, text: str) -> Optional[str]:
        """Translate using Google Translate HTTP API (network required).

        Uses the free translate.googleapis.com endpoint (no API key required).
        """
        if not self._network_enabled:
            logger.warning("Google Translate HTTP disabled (LINGVIST_TRANSLATIONS_NETWORK_ENABLED=false)")
            return None

        if not text or not text.strip():
            return None

        try:
            # Build URL: https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=pt&dt=t&q=<text>
            base_url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "en",  # source language
                "tl": self._target_lang,  # target language
                "dt": "t",  # return translation
                "q": text.strip()
            }

            # Make request with timeout
            timeout = httpx.Timeout(self._timeout_s)
            with httpx.Client(timeout=timeout) as client:
                response = client.get(base_url, params=params)
                response.raise_for_status()

                # Parse JSON response: [[["translation", "source_text", ...]], ...]
                data = response.json()
                if data and data[0]:
                    # Concatenate all translated segments
                    translated = "".join([item[0] for item in data[0]])
                    logger.debug(f"Google HTTP: '{text[:50]}...' → '{translated[:50]}...'")
                    return translated.strip()
                else:
                    logger.warning(f"Google Translate returned empty response for '{text[:50]}...'")
                    return None

        except httpx.TimeoutException:
            logger.error(f"Google Translate HTTP timeout after {self._timeout_s}s for '{text[:50]}...'")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Google Translate HTTP error {e.response.status_code} for '{text[:50]}...'")
            return None
        except Exception as e:
            logger.error(f"Google Translate HTTP failed for '{text[:50]}...': {e}")
            return None

    def translate(self, text: str) -> Optional[str]:
        """Translate text from English to target language.

        Provider selection:
        - If provider is "argos": use Argos Translate (offline)
        - If provider is "google_http": use Google Translate HTTP API (network)
        - Falls back to None if provider fails

        Args:
            text: English text to translate

        Returns:
            Translated text, or None if translation fails/is disabled
        """
        if not self._enabled or not text or not text.strip():
            return None

        # Route to appropriate provider
        if self._provider == "argos":
            return self._translate_with_argos(text)
        elif self._provider == "google_http":
            return self._translate_with_google_http(text)
        else:
            logger.warning(f"Unknown translation provider: {self._provider}")
            return None

    def is_enabled(self) -> bool:
        """Check if translation service is enabled."""
        return self._enabled

    def is_initialized(self) -> bool:
        """Check if translation service is initialized."""
        if self._provider == "argos":
            return self._argos_initialized
        elif self._provider == "google_http":
            # Google HTTP doesn't need initialization
            return True
        return False

    def get_provider(self) -> str:
        """Get current provider name."""
        return self._provider


# Singleton instance
_translation_service = TranslationService()


def get_translation_service() -> TranslationService:
    """Get singleton translation service instance."""
    return _translation_service
