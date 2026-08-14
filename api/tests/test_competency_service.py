from types import SimpleNamespace

from app.pedagogy.catalog import infer_primary_skill
from app.services.competency_service import scaffold_level, update_skill_state


def test_infer_primary_skill_prefers_explicit_grammar_signal():
    definition = infer_primary_skill(
        language_code="en",
        part_of_speech="verb",
        features={"tense": "past"},
        sentence_text="I ___ there yesterday.",
    )
    assert definition.code == "en.grammar.past_simple"


def test_update_skill_state_discounts_supported_success():
    independent = SimpleNamespace(
        observation_count=0,
        success_weight=0.0,
        evidence_weight=0.0,
        mastery_probability=0.5,
        confidence=0.0,
        independent_success_count=0,
        independent_attempt_count=0,
        independent_success_rate=0.0,
        last_observed_at=None,
        next_practice_at=None,
        model_version="",
    )
    supported = SimpleNamespace(**independent.__dict__)
    update_skill_state(independent, score=1.0, was_independent=True)
    update_skill_state(supported, score=0.55, was_independent=False)
    assert independent.mastery_probability > supported.mastery_probability
    assert independent.independent_success_rate == 1.0
    assert supported.independent_success_rate == 0.0
    assert independent.independent_attempt_count == 1
    assert supported.independent_attempt_count == 0
    assert scaffold_level(0, 1) == "independent"
    assert scaffold_level(3, 3) == "high_support"
