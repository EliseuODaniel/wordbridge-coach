"""On-demand translation autofill for Lingvist payloads."""

from __future__ import annotations

import logging
import os
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Card, Sentence, Word
from app.services.translation_service import get_translation_service

logger = logging.getLogger(__name__)

_tsv_translations_cache: Optional[dict[str, str]] = None


def load_tsv_translations(tsv_path: str = "/app/data/en_pt_word_translations_sample.tsv") -> dict[str, str]:
    """Load curated EN-PT translations from TSV only once per process."""
    global _tsv_translations_cache

    if _tsv_translations_cache is not None:
        return _tsv_translations_cache

    _tsv_translations_cache = {}
    if not os.path.exists(tsv_path):
        logger.info("TSV file not found: %s", tsv_path)
        return _tsv_translations_cache

    try:
        logger.info("Loading TSV translations from %s...", tsv_path)
        with open(tsv_path, "r", encoding="utf-8") as file_obj:
            for line in file_obj:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split("\t")
                if len(parts) < 2:
                    continue

                word = parts[0].strip().lower()
                pt_translation = parts[1].strip()
                if not word or not pt_translation:
                    continue

                _tsv_translations_cache[word] = pt_translation

        logger.info("Loaded %s TSV translations", len(_tsv_translations_cache))
    except Exception as error:
        logger.error("Failed to load TSV translations: %s", error)

    return _tsv_translations_cache


def autofill_translations(db: Session, word: Word, sentence: Sentence, card: Card) -> None:
    """Fill missing word and sentence translations using TSV overrides and MT."""
    translation_service = get_translation_service()
    tsv_override = load_tsv_translations()

    word_needs_translation = (
        not word.features
        or not isinstance(word.features, dict)
        or not word.features.get("pt_translation")
        or not word.features["pt_translation"].strip()
    )

    if word_needs_translation:
        word_translation = None
        word_lower = word.lemma.lower() if word.lemma else ""

        if word_lower in tsv_override:
            word_translation = tsv_override[word_lower]
            logger.info("Word translation from TSV: %s -> %s", word.lemma, word_translation)
        elif translation_service.is_enabled():
            word_translation = translation_service.translate(word.lemma or word.text)
            if word_translation:
                logger.info(
                    "Word translation from %s: %s -> %s",
                    translation_service.get_provider(),
                    word.lemma,
                    word_translation,
                )

        if word_translation:
            if not word.features or not isinstance(word.features, dict):
                word.features = {}
            word.features["pt_translation"] = word_translation
            db.flush()

    sentence_needs_translation = not sentence.translation or not sentence.translation.strip()
    if sentence_needs_translation and translation_service.is_enabled():
        sentence_with_word = (sentence.text or "").replace("___", word.text or "", 1)
        sentence_translation = translation_service.translate(sentence_with_word)
        if sentence_translation:
            logger.info(
                "Sentence translation from %s: '%s...' -> '%s...'",
                translation_service.get_provider(),
                sentence_with_word[:50],
                sentence_translation[:50],
            )
            sentence.translation = sentence_translation
            db.flush()
