"""Translation service using Argos Translate for offline MT.

This service provides English→Portuguese translations on-demand with caching
in the database to avoid re-translation.
"""

import logging
from typing import Optional
from decouple import config

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translating text using Argos Translate (offline MT)."""

    def __init__(self):
        self._translator = None
        self._enabled = config("LINGVIST_TRANSLATIONS_AUTOFILL", default=False, cast=bool)
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of Argos Translate (downloads models on first use)."""
        if self._initialized or not self._enabled:
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
                if pkg.from_code == "en" and pkg.to_code == "pt"
            ]

            if not en_to_pt_packages:
                logger.error("EN→PT translation package not found in Argos Translate")
                return

            # Download first available package
            en_to_pt_package = en_to_pt_packages[0]
            logger.info(f"Downloading package: {en_to_pt_package.package_version}")
            argostranslate.package.install_from_path(en_to_pt_package.download())

            # Create translator
            from_translation = "en"
            to_translation = "pt"
            self._translator = argostranslate.translate.get_translation_from_code(
                from_translation, to_translation
            )

            self._initialized = True
            logger.info("✅ Argos Translate initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Argos Translate: {e}")
            self._enabled = False  # Disable on error

    def translate(self, text: str) -> Optional[str]:
        """Translate text from English to Portuguese.

        Args:
            text: English text to translate

        Returns:
            Portuguese translation, or None if translation fails/is disabled
        """
        if not self._enabled or not text or not text.strip():
            return None

        try:
            self._ensure_initialized()

            if not self._translator:
                logger.warning("Translator not initialized, skipping translation")
                return None

            # Translate
            translated = self._translator.translate(text.strip())
            logger.debug(f"Translated: '{text}' → '{translated}'")
            return translated

        except Exception as e:
            logger.error(f"Translation failed for '{text}': {e}")
            return None

    def is_enabled(self) -> bool:
        """Check if translation service is enabled."""
        return self._enabled

    def is_initialized(self) -> bool:
        """Check if translation service is initialized (models downloaded)."""
        return self._initialized


# Singleton instance
_translation_service = TranslationService()


def get_translation_service() -> TranslationService:
    """Get singleton translation service instance."""
    return _translation_service
