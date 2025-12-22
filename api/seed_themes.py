#!/usr/bin/env python3
"""
Quick script to populate basic themes and mappings for FillTheWord
"""

import sys
import os
import uuid
from datetime import datetime

# Add the parent directory to the path to import app modules
sys.path.append('/app')

from app.core.database import SessionLocal
from app.models import (
    WordTheme, WordThemeMapping, Word, Language
)
from sqlalchemy.orm import Session

def create_basic_themes(db: Session):
    """Create basic word themes"""
    print("Creating basic themes...")

    themes_data = [
        {"name": "Daily Actions", "description": "Common everyday actions and verbs"},
        {"name": "House & Home", "description": "Words related to home, furniture, and daily living"},
        {"name": "Food & Drink", "description": "Food, beverages, and eating-related vocabulary"},
        {"name": "People & Family", "description": "People, family members, and relationships"},
        {"name": "Time & Weather", "description": "Time expressions and weather-related words"},
        {"name": "School & Learning", "description": "Education, school, and learning vocabulary"},
        {"name": "Basic Nouns", "description": "Essential nouns for everyday conversation"},
        {"name": "Basic Adjectives", "description": "Common descriptive words"},
        {"name": "Question Words", "description": "Words used to ask questions"},
        {"name": "Connecting Words", "description": "Conjunctions and connectors"},
    ]

    created_themes = []
    for theme_data in themes_data:
        existing_theme = db.query(WordTheme).filter(WordTheme.name == theme_data["name"]).first()
        if not existing_theme:
            theme = WordTheme(
                id=str(uuid.uuid4()),
                name=theme_data["name"],
                description=theme_data["description"],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(theme)
            created_themes.append(theme)
            print(f"  Created theme: {theme_data['name']}")

    db.commit()
    return created_themes


def map_words_to_themes(db: Session):
    """Map existing words to appropriate themes"""
    print("Mapping words to themes...")

    # Get themes by name
    daily_actions = db.query(WordTheme).filter(WordTheme.name == "Daily Actions").first()
    house_home = db.query(WordTheme).filter(WordTheme.name == "House & Home").first()
    food_drink = db.query(WordTheme).filter(WordTheme.name == "Food & Drink").first()
    people_family = db.query(WordTheme).filter(WordTheme.name == "People & Family").first()
    time_weather = db.query(WordTheme).filter(WordTheme.name == "Time & Weather").first()
    school_learning = db.query(WordTheme).filter(WordTheme.name == "School & Learning").first()
    basic_nouns = db.query(WordTheme).filter(WordTheme.name == "Basic Nouns").first()
    basic_adjectives = db.query(WordTheme).filter(WordTheme.name == "Basic Adjectives").first()
    question_words = db.query(WordTheme).filter(WordTheme.name == "Question Words").first()
    connecting_words = db.query(WordTheme).filter(WordTheme.name == "Connecting Words").first()

    # Theme mappings for common words
    word_mappings = [
        # Daily Actions
        ("be", daily_actions), ("have", daily_actions), ("do", daily_actions),
        ("go", daily_actions), ("come", daily_actions), ("make", daily_actions),
        ("take", daily_actions), ("give", daily_actions), ("get", daily_actions),
        ("see", daily_actions), ("look", daily_actions), ("say", daily_actions),
        ("tell", daily_actions), ("ask", daily_actions), ("work", daily_actions),
        ("play", daily_actions), ("read", daily_actions), ("write", daily_actions),

        # House & Home
        ("house", house_home), ("home", house_home), ("table", house_home),
        ("book", house_home), ("water", house_home), ("door", house_home),
        ("room", house_home), ("kitchen", house_home), ("bed", house_home),

        # Basic Nouns
        ("man", basic_nouns), ("woman", basic_nouns), ("child", basic_nouns),
        ("friend", basic_nouns), ("cat", basic_nouns), ("dog", basic_nouns),
        ("time", basic_nouns), ("day", basic_nouns), ("year", basic_nouns),
        ("way", basic_nouns), ("thing", basic_nouns), ("world", basic_nouns),
        ("life", basic_nouns), ("hand", basic_nouns), ("part", basic_nouns),
        ("place", basic_nouns), ("case", basic_nouns), ("week", basic_nouns),
        ("point", basic_nouns), ("company", basic_nouns), ("group", basic_nouns),
        ("problem", basic_nouns), ("service", basic_nouns), ("important", basic_nouns),

        # Basic Adjectives
        ("good", basic_adjectives), ("new", basic_adjectives), ("first", basic_adjectives),
        ("last", basic_adjectives), ("long", basic_adjectives), ("great", basic_adjectives),
        ("little", basic_adjectives), ("own", basic_adjectives), ("other", basic_adjectives),
        ("old", basic_adjectives), ("right", basic_adjectives), ("big", basic_adjectives),
        ("high", basic_adjectives), ("different", basic_adjectives), ("small", basic_adjectives),
        ("large", basic_adjectives), ("next", basic_adjectives), ("early", basic_adjectives),
        ("young", basic_adjectives), ("important", basic_adjectives), ("few", basic_adjectives),
        ("public", basic_adjectives), ("bad", basic_adjectives), ("same", basic_adjectives),
        ("able", basic_adjectives),

        # Connecting Words
        ("the", connecting_words), ("and", connecting_words), ("a", connecting_words),
        ("in", connecting_words), ("that", connecting_words), ("have", connecting_words),
        ("i", connecting_words), ("it", connecting_words), ("for", connecting_words),
        ("not", connecting_words), ("on", connecting_words), ("with", connecting_words),
        ("he", connecting_words), ("as", connecting_words), ("you", connecting_words),
        ("do", connecting_words), ("at", connecting_words), ("this", connecting_words),
        ("but", connecting_words), ("his", connecting_words), ("by", connecting_words),
        ("from", connecting_words), ("they", connecting_words), ("we", connecting_words),
        ("say", connecting_words), ("her", connecting_words), ("she", connecting_words),
        ("or", connecting_words), ("an", connecting_words), ("will", connecting_words),
        ("my", connecting_words), ("one", connecting_words), ("all", connecting_words),
        ("would", connecting_words), ("there", connecting_words), ("their", connecting_words),
        ("what", connecting_words), ("so", connecting_words), ("up", connecting_words),
        ("out", connecting_words), ("if", connecting_words), ("about", connecting_words),
        ("who", connecting_words), ("get", connecting_words), ("which", connecting_words),
        ("go", connecting_words), ("me", connecting_words), ("when", connecting_words),
        ("make", connecting_words), ("can", connecting_words), ("like", connecting_words),
        ("time", connecting_words), ("no", connecting_words), ("just", connecting_words),
        ("him", connecting_words), ("know", connecting_words), ("take", connecting_words),
        ("people", connecting_words), ("into", connecting_words), ("year", connecting_words),
        ("your", connecting_words), ("good", connecting_words), ("some", connecting_words),
        ("could", connecting_words), ("them", connecting_words), ("see", connecting_words),
        ("other", connecting_words), ("than", connecting_words), ("then", connecting_words),
        ("now", connecting_words), ("look", connecting_words), ("only", connecting_words),
        ("come", connecting_words), ("its", connecting_words), ("over", connecting_words),
        ("think", connecting_words), ("also", connecting_words), ("back", connecting_words),
        ("after", connecting_words), ("use", connecting_words), ("two", connecting_words),
        ("how", connecting_words), ("our", connecting_words), ("work", connecting_words),
        ("first", connecting_words), ("well", connecting_words), ("way", connecting_words),
        ("even", connecting_words), ("new", connecting_words), ("want", connecting_words),
        ("because", connecting_words), ("any", connecting_words), ("these", connecting_words),
        ("give", connecting_words), ("day", connecting_words), ("most", connecting_words),
        ("us", connecting_words),

        # French words (map to appropriate themes)
        ("le", connecting_words), ("être", daily_actions), ("et", connecting_words),
        ("à", connecting_words), ("les", connecting_words), ("de", connecting_words),
        ("un", basic_adjectives), ("il", people_family), ("pour", connecting_words),
        ("que", connecting_words), ("avoir", daily_actions), ("dans", connecting_words),
        ("ce", connecting_words), ("son", people_family), ("une", basic_adjectives),
        ("sur", connecting_words), ("avec", connecting_words), ("ne", connecting_words),
        ("se", people_family), ("pas", connecting_words), ("tout", basic_adjectives),
        ("pouvoir", daily_actions), ("plus", connecting_words), ("par", connecting_words),
        ("grand", basic_adjectives), ("mais", connecting_words), ("me", people_family),
        ("comme", connecting_words), ("même", basic_adjectives), ("bien", basic_adjectives),
    ]

    mappings_created = 0
    for word_text, theme in word_mappings:
        if not theme:
            continue

        # Find the word
        word = db.query(Word).filter(Word.text == word_text).first()
        if word and theme:
            # Check if mapping already exists
            existing_mapping = db.query(WordThemeMapping).filter(
                WordThemeMapping.word_id == word.id,
                WordThemeMapping.theme_id == theme.id
            ).first()

            if not existing_mapping:
                mapping = WordThemeMapping(
                    id=str(uuid.uuid4()),
                    word_id=word.id,
                    theme_id=theme.id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(mapping)
                mappings_created += 1

    db.commit()
    print(f"  Created {mappings_created} word-theme mappings")


def main():
    """Main function to populate themes and mappings"""
    print("🏷️  Starting theme population...")

    db = SessionLocal()
    try:
        # Create themes
        themes = create_basic_themes(db)
        print(f"✅ Created {len(themes)} themes")

        # Create mappings
        map_words_to_themes(db)
        print("✅ Created word-theme mappings")

        print("🎉 Theme population completed successfully!")

    except Exception as e:
        print(f"❌ Error populating themes: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()