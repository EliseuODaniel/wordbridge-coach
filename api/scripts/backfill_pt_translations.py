#!/usr/bin/env python3
"""
Backfill PT translations for English words from TSV file.

This script reads en_pt_word_translations_sample.tsv and updates
Word.features['pt_translation'] for English words that don't have it yet.
"""

import sys
import os

sys.path.append('/app')

from app.core.database import SessionLocal
from app.models import Word, Language


def load_pt_translations_from_tsv(tsv_path: str) -> dict[str, dict]:
    """
    Load PT translations from TSV file.

    Returns:
        Dict mapping lowercase word -> {pt_translation, part_of_speech}
    """
    translations = {}

    if not os.path.exists(tsv_path):
        print(f"⚠️  Translation file not found: {tsv_path}")
        return translations

    print(f"📚 Loading translations from {tsv_path}...")

    with open(tsv_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            parts = line.split('\t')
            if len(parts) < 2:
                print(f"⚠️  Skipping invalid line {line_num}: {line[:50]}...")
                continue

            word = parts[0].strip()
            pt_translation = parts[1].strip()
            part_of_speech = parts[2].strip() if len(parts) > 2 else None

            # Skip empty translations
            if not pt_translation:
                continue

            # Store with lowercase key for matching
            translations[word.lower()] = {
                'pt_translation': pt_translation,
                'part_of_speech': part_of_speech
            }

    print(f"✅ Loaded {len(translations)} translations from TSV")
    return translations


def backfill_pt_translations(translations: dict[str, dict], dry_run: bool = False):
    """
    Backfill PT translations for English words.

    Args:
        translations: Dict mapping word -> {pt_translation, part_of_speech}
        dry_run: If True, don't commit changes
    """
    db = SessionLocal()

    try:
        # Get English language
        en_lang = db.query(Language).filter(Language.code == 'en').first()
        if not en_lang:
            print("❌ English language not found!")
            return

        # Get all English words
        words = db.query(Word).filter(Word.language_id == en_lang.id).all()
        print(f"📊 Found {len(words)} English words")

        updated_count = 0
        pos_updated_count = 0
        skipped_count = 0

        for word in words:
            word_lower = word.lemma.lower()

            # Check if we have a translation for this word
            if word_lower not in translations:
                skipped_count += 1
                continue

            trans = translations[word_lower]

            # Initialize features if None
            if word.features is None:
                word.features = {}

            # Skip if already has pt_translation (don't overwrite)
            if word.features.get('pt_translation'):
                skipped_count += 1
                continue

            # Update pt_translation
            word.features['pt_translation'] = trans['pt_translation']
            updated_count += 1

            # Update part_of_speech if UNK and we have a better one
            if word.part_of_speech == 'UNK' and trans.get('part_of_speech'):
                word.part_of_speech = trans['part_of_speech']
                pos_updated_count += 1

        if dry_run:
            print(f"\n🔍 DRY RUN - Would update {updated_count} words")
            print(f"🔍 Would update {pos_updated_count} part_of_speech tags")
            db.rollback()
        else:
            db.commit()
            print(f"\n✅ Updated {updated_count} words with PT translations")
            print(f"✅ Updated {pos_updated_count} part_of_speech tags")
            print(f"⏭️  Skipped {skipped_count} words (already had translation or not in TSV)")

        # Show statistics
        print(f"\n📊 Statistics:")
        print(f"   Total words: {len(words)}")
        print(f"   Updated: {updated_count}")
        print(f"   Skipped: {skipped_count}")
        if updated_count > 0:
            percentage = 100.0 * updated_count / len(words)
            print(f"   Coverage: {percentage:.1f}%")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main entry point."""
    tsv_path = "/app/data/en_pt_word_translations_sample.tsv"

    print("=" * 60)
    print("PT Translation Backfill for English Words")
    print("=" * 60)

    # Load translations
    translations = load_pt_translations_from_tsv(tsv_path)

    if not translations:
        print("❌ No translations loaded, exiting.")
        return

    # Backfill
    print("\n" + "=" * 60)
    print("Backfilling translations...")
    print("=" * 60)

    import argparse
    parser = argparse.ArgumentParser(description='Backfill PT translations')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without committing')
    parser.add_argument('--commit', action='store_true', help='Commit changes to database')

    args = parser.parse_args()

    if args.dry_run:
        backfill_pt_translations(translations, dry_run=True)
    elif args.commit:
        backfill_pt_translations(translations, dry_run=False)
    else:
        print("\n⚠️  No action specified. Use --commit to apply changes.")
        print("   Use --dry-run to preview changes.")


if __name__ == '__main__':
    main()
