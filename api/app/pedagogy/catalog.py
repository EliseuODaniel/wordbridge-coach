"""Versioned instructional competency catalog for adult English learners."""

from __future__ import annotations

from dataclasses import dataclass


CATALOG_VERSION = "en-core-v1"


@dataclass(frozen=True)
class SkillDefinition:
    code: str
    language_code: str
    name: str
    description: str
    framework_level: str
    modality: str
    can_do_descriptor: str
    concept_tags: tuple[str, ...]


ENGLISH_CORE_SKILLS = (
    SkillDefinition(
        "en.lexical.high_frequency", "en", "High-frequency vocabulary in context",
        "Recognize and retrieve common words inside short meaningful utterances.",
        "A1", "reading_writing",
        "Can understand and use familiar everyday words in short contextualized sentences.",
        ("vocabulary", "retrieval", "context"),
    ),
    SkillDefinition(
        "en.grammar.articles", "en", "Articles in noun phrases",
        "Choose a, an, the, or no article in common concrete contexts.",
        "A1", "reading_writing",
        "Can form simple noun phrases for familiar people, places, and objects.",
        ("grammar", "articles", "noun_phrase"),
    ),
    SkillDefinition(
        "en.grammar.prepositions", "en", "Basic prepositions",
        "Use frequent prepositions for location, time, and movement.",
        "A1", "reading_writing",
        "Can describe basic location, time, and movement with familiar expressions.",
        ("grammar", "prepositions", "location", "movement"),
    ),
    SkillDefinition(
        "en.grammar.present_simple", "en", "Present simple",
        "Describe routines, states, and repeated actions with basic agreement.",
        "A1", "reading_writing",
        "Can give simple information about routines and everyday facts.",
        ("grammar", "verb", "present_simple"),
    ),
    SkillDefinition(
        "en.interaction.questions", "en", "Everyday questions",
        "Form and understand common questions and short answers.",
        "A2", "interaction",
        "Can ask and answer straightforward questions about familiar matters.",
        ("interaction", "questions", "auxiliaries"),
    ),
    SkillDefinition(
        "en.grammar.past_simple", "en", "Past-time reference",
        "Refer to completed past events using common regular and irregular forms.",
        "A2", "reading_writing",
        "Can describe in simple terms a past event or personal experience.",
        ("grammar", "verb", "past_simple"),
    ),
    SkillDefinition(
        "en.lexical.collocations", "en", "Common collocations",
        "Retrieve common multiword units rather than translating isolated words.",
        "A2", "reading_writing",
        "Can use common phrases and lexical combinations in routine situations.",
        ("vocabulary", "collocation", "chunks"),
    ),
    SkillDefinition(
        "en.writing.connected_sentences", "en", "Connected sentences",
        "Connect short clauses to explain or narrate with basic cohesion.",
        "B1", "writing",
        "Can write connected text on familiar topics and personal experiences.",
        ("writing", "cohesion", "sentence_connection"),
    ),
    SkillDefinition(
        "en.speaking.read_aloud_intelligibility", "en", "Read-aloud intelligibility",
        "Produce a practiced sentence clearly enough for robust transcription.",
        "A1", "speaking",
        "Can pronounce a limited repertoire of familiar words and phrases intelligibly.",
        ("speaking", "intelligibility", "read_aloud"),
    ),
)

CATALOGS = {"en": ENGLISH_CORE_SKILLS}


def get_catalog(language_code: str) -> tuple[SkillDefinition, ...]:
    return CATALOGS.get(language_code.casefold(), ())


def get_skill_definition(code: str) -> SkillDefinition | None:
    return next(
        (definition for catalog in CATALOGS.values() for definition in catalog if definition.code == code),
        None,
    )


def infer_primary_skill(*, language_code: str, part_of_speech: str, features: dict | None, sentence_text: str) -> SkillDefinition | None:
    """Map legacy content to one primary skill conservatively."""
    if language_code != "en":
        return None
    features = features if isinstance(features, dict) else {}
    text = (sentence_text or "").casefold()
    tense = str(features.get("tense") or "").casefold()
    pos = (part_of_speech or "").casefold()
    if pos == "article":
        code = "en.grammar.articles"
    elif pos == "preposition":
        code = "en.grammar.prepositions"
    elif tense == "past" or any(marker in text for marker in ("yesterday", "last week", "ago")):
        code = "en.grammar.past_simple"
    elif "?" in text:
        code = "en.interaction.questions"
    elif pos == "verb":
        code = "en.grammar.present_simple"
    else:
        code = "en.lexical.high_frequency"
    return get_skill_definition(code)
