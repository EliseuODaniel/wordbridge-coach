#!/usr/bin/env python3
"""Idempotently load the reviewed WordBridge contemporary English pack."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import Deck, Language
from app.services.curated_content_seed_service import seed_curated_english_content


def main() -> None:
    db = SessionLocal()
    try:
        language = db.query(Language).filter(Language.code == "en").first()
        if not language:
            raise RuntimeError("English language row is required before curated content can be seeded")
        deck = db.query(Deck).filter(
            Deck.language_id == language.id,
            Deck.is_active == True,
        ).order_by(Deck.created_at.asc()).first()
        if not deck:
            raise RuntimeError("An active English deck is required before curated content can be seeded")

        sentences, cards = seed_curated_english_content(
            db,
            language_id=language.id,
            deck=deck,
        )
        db.commit()
        print(f"Curated content ready: {len(sentences)} sentences and {len(cards)} cards created")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
