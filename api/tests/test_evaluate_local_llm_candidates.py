from scripts.evaluate_local_llm_candidates import (
    all_portuguese,
    check_correct,
    check_past,
    portuguese,
)
from app.llm.pedagogical_tasks import normalize_draft_evaluation


def _evaluation(*, draft: str, issues: list[dict], grammar_score: float = 75) -> dict:
    return {
        "grammar_score": grammar_score,
        "spelling_score": 100,
        "naturalness_score": 90,
        "lesson_alignment_score": 95,
        "top_issues": issues,
        "suggested_next_words": [],
        "micro_tip": "Lembre de usar o passado nesta frase.",
        "self_check_prompt": "Você usou a forma correta do verbo?",
        "encouragement": "Muito bom, continue praticando.",
        "topic": "past experiences",
        "intent": "practice past tense",
        "rewrite": draft,
    }


def test_portuguese_detector_rejects_english_feedback() -> None:
    assert portuguese("Você usou a forma correta do verbo?") is True
    assert portuguese("Use the correct past form of the verb.") is False
    assert all_portuguese([
        "Você usou a forma correta do verbo?",
        "Muito bom, continue praticando.",
    ]) is True
    assert all_portuguese([
        "Você usou a forma correta do verbo?",
        "Use the correct past form of the verb.",
    ]) is False
    assert portuguese("Conjugação de verbos no passado simples") is True


def test_past_check_rejects_goed_and_accepts_went() -> None:
    draft = "Yesterday I go to the museum."
    valid = _evaluation(
        draft="Yesterday I went to the museum.",
        issues=[{
            "category": "grammar",
            "title": "Past tense",
            "explanation": "Use a forma correta do verbo no passado.",
            "highlight_text": "go",
            "suggestions": ["went"],
        }],
    )
    invalid = {**valid, "top_issues": [{**valid["top_issues"][0], "suggestions": ["goed"]}]}

    assert all(check_past(valid, draft).values()) is True
    assert check_past(invalid, draft)["no_regular_ed_for_go"] is False


def test_past_check_accepts_an_exact_phrase_highlight_containing_go() -> None:
    draft = "Yesterday I go to the museum."
    valid = _evaluation(
        draft="Yesterday I went to the museum.",
        issues=[{
            "category": "grammar",
            "title": "Past tense",
            "explanation": "Use a forma correta do verbo no passado.",
            "highlight_text": "Yesterday I go",
            "suggestions": ["Yesterday I went"],
        }],
    )

    assert all(check_past(valid, draft).values()) is True


def test_correct_sentence_check_requires_no_false_issues() -> None:
    draft = "Yesterday I went to the museum with my sister."
    valid = _evaluation(draft=draft, issues=[], grammar_score=98)
    false_positive = {
        **valid,
        "top_issues": [{
            "category": "style",
            "title": "Verb tense",
            "explanation": "A frase já está correta no passado.",
            "highlight_text": "went",
            "suggestions": ["go"],
        }],
    }

    assert all(check_correct(valid, draft).values()) is True
    assert check_correct(false_positive, draft)["no_false_issue"] is False


def test_normalization_removes_invalid_highlights_and_explicit_false_issues() -> None:
    draft = "Yesterday I went to the museum with my sister."
    payload = _evaluation(
        draft=draft,
        grammar_score=95,
        issues=[{
            "category": "grammar",
            "title": "Optional enrichment",
            "explanation": "A frase está gramaticalmente correta como está.",
            "highlight_text": "Yesterday I visited",
            "suggestions": [draft, draft],
        }],
    )

    normalized = normalize_draft_evaluation(payload, draft)

    assert normalized["top_issues"] == []


def test_normalization_deduplicates_exact_issue_highlights() -> None:
    draft = "Yesterday I go to the museum."
    issue = {
        "category": "grammar",
        "title": "Past tense",
        "explanation": "Use a forma correta do verbo no passado.",
        "highlight_text": "Yesterday I go",
        "suggestions": ["Yesterday I went", "Yesterday I went"],
    }
    payload = _evaluation(draft=draft, issues=[issue, {**issue, "title": "Repeated"}])

    normalized = normalize_draft_evaluation(payload, draft)

    assert len(normalized["top_issues"]) == 1
    assert normalized["top_issues"][0]["suggestions"] == ["Yesterday I went"]


def test_normalization_drops_optional_enrichment_labeled_as_grammar_issue() -> None:
    draft = "Yesterday I went to the museum with my sister."
    payload = _evaluation(
        draft=draft,
        grammar_score=95,
        issues=[{
            "category": "grammar",
            "title": "Verb tense consistency",
            "explanation": "A frase pode ser melhorada para enfatizar a duração da visita.",
            "highlight_text": "went to the museum",
            "suggestions": ["visited the museum"],
        }],
    )

    assert normalize_draft_evaluation(payload, draft)["top_issues"] == []
