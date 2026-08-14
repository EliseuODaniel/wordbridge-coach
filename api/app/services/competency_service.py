"""Competency mapping, evidence updates, and honest proficiency summaries."""

from __future__ import annotations

from datetime import timedelta
import math

from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models import LearnerSkillState, LearningSkill, PedagogicalObservation, SentenceSkill
from app.pedagogy.catalog import CATALOG_VERSION, SkillDefinition, get_catalog, infer_primary_skill


MODEL_VERSION = "beta-evidence-v1"
POLICY_VERSION = "pedagogy-policy-v1"


def ensure_skill(db: Session, definition: SkillDefinition) -> LearningSkill:
    skill = db.query(LearningSkill).filter(LearningSkill.code == definition.code).first()
    if skill:
        return skill
    skill = LearningSkill(
        code=definition.code,
        language_code=definition.language_code,
        name=definition.name,
        description=definition.description,
        framework="CEFR",
        framework_level=definition.framework_level,
        modality=definition.modality,
        can_do_descriptor=definition.can_do_descriptor,
        concept_tags=list(definition.concept_tags),
        catalog_version=CATALOG_VERSION,
        is_active=True,
    )
    db.add(skill)
    db.flush()
    return skill


def ensure_catalog(db: Session, language_code: str) -> list[LearningSkill]:
    return [ensure_skill(db, definition) for definition in get_catalog(language_code)]


def resolve_card_skill(db: Session, card) -> LearningSkill | None:
    sentence = getattr(card, "sentence", None)
    word = getattr(sentence, "word", None)
    if not sentence or not word:
        return None
    mapping = db.query(SentenceSkill).filter(
        SentenceSkill.sentence_id == sentence.id,
        SentenceSkill.role == "primary",
    ).first()
    if mapping:
        return db.query(LearningSkill).filter(LearningSkill.id == mapping.skill_id).first()

    language = getattr(word, "language", None) or getattr(sentence, "language", None)
    language_code = str(getattr(language, "code", "") or "").casefold()
    if not language_code:
        return None
    explicit_codes = sentence.competency_codes if isinstance(sentence.competency_codes, list) else []
    definition = next(
        (candidate for candidate in get_catalog(language_code) if explicit_codes and candidate.code == explicit_codes[0]),
        None,
    )
    definition = definition or infer_primary_skill(
        language_code=language_code,
        part_of_speech=str(getattr(word, "part_of_speech", "") or ""),
        features=getattr(word, "features", None),
        sentence_text=str(getattr(sentence, "text", "") or ""),
    )
    if definition is None:
        return None
    skill = ensure_skill(db, definition)
    db.add(SentenceSkill(
        sentence_id=sentence.id,
        skill_id=skill.id,
        role="primary",
        weight=1.0,
        mapping_source="explicit_metadata" if explicit_codes else "catalog_heuristic_v1",
    ))
    db.flush()
    return skill


def _get_or_create_state(db: Session, user_id, skill_id) -> LearnerSkillState:
    state = db.query(LearnerSkillState).filter(
        LearnerSkillState.user_id == user_id,
        LearnerSkillState.skill_id == skill_id,
    ).first()
    if state:
        return state
    state = LearnerSkillState(user_id=user_id, skill_id=skill_id)
    db.add(state)
    db.flush()
    return state


def scaffold_level(hints_used: int, attempts: int) -> str:
    if hints_used <= 0 and attempts <= 1:
        return "independent"
    if hints_used <= 2 and attempts <= 2:
        return "guided"
    return "high_support"


def update_skill_state(state: LearnerSkillState, *, score: float, was_independent: bool, observed_at=None) -> None:
    """Update an interpretable beta-evidence estimate."""
    now = observed_at or utc_now()
    bounded_score = max(0.0, min(1.0, float(score)))
    state.observation_count = int(state.observation_count or 0) + 1
    state.success_weight = float(state.success_weight or 0.0) + bounded_score
    state.evidence_weight = float(state.evidence_weight or 0.0) + 1.0
    state.mastery_probability = round((1.0 + state.success_weight) / (2.0 + state.evidence_weight), 4)
    state.confidence = round(1.0 - math.exp(-state.evidence_weight / 6.0), 4)
    if was_independent:
        state.independent_attempt_count = int(state.independent_attempt_count or 0) + 1
        if bounded_score >= 0.999:
            state.independent_success_count = int(state.independent_success_count or 0) + 1
    state.independent_success_rate = round(
        state.independent_success_count / max(state.independent_attempt_count, 1),
        4,
    )
    state.last_observed_at = now
    delay = timedelta(days=7 if state.mastery_probability >= 0.85 else 3 if state.mastery_probability >= 0.70 else 1)
    state.next_practice_at = now + delay
    state.model_version = MODEL_VERSION


def record_card_observation(db: Session, *, user_id, card, answer_data, was_correct: bool) -> PedagogicalObservation:
    skill = resolve_card_skill(db, card)
    hints = max(0, int(answer_data.hints_used or 0))
    attempts = max(1, int(answer_data.attempts or 1))
    independence = hints == 0 and attempts == 1
    score = max(0.35, 1.0 - (0.12 * hints) - (0.15 * (attempts - 1))) if was_correct else 0.0
    mode = str(getattr(answer_data, "mode", "spec4") or "spec4")
    task_type = str(getattr(answer_data, "task_type", "gap_recall") or "gap_recall")
    observation = PedagogicalObservation(
        user_id=user_id,
        skill_id=skill.id if skill else None,
        card_id=card.id,
        sentence_id=card.sentence.id,
        session_id=getattr(answer_data, "session_id", None),
        event_type="answer_submitted",
        mode=mode,
        task_type=task_type,
        modality="reading_writing",
        was_correct=was_correct,
        score=score,
        hints_used=hints,
        attempts=attempts,
        response_time_ms=answer_data.response_time_ms,
        scaffold_level=scaffold_level(hints, attempts),
        was_independent=independence,
        learner_answer=answer_data.answer,
        policy_version=POLICY_VERSION,
        model_version=MODEL_VERSION,
        metadata_json={"answer_validation": "normalized_exact_or_allowed_variant"},
    )
    db.add(observation)
    if skill:
        update_skill_state(
            _get_or_create_state(db, user_id, skill.id),
            score=score,
            was_independent=independence,
        )
    return observation


def build_card_competency_context(db: Session, *, user_id, card) -> dict | None:
    skill = resolve_card_skill(db, card)
    if not skill:
        return None
    state = db.query(LearnerSkillState).filter(
        LearnerSkillState.user_id == user_id,
        LearnerSkillState.skill_id == skill.id,
    ).first()
    return {
        "code": skill.code,
        "name": skill.name,
        "framework": skill.framework,
        "framework_level": skill.framework_level,
        "modality": skill.modality,
        "can_do_descriptor": skill.can_do_descriptor,
        "mastery_probability": float(state.mastery_probability) if state else 0.5,
        "confidence": float(state.confidence) if state else 0.0,
        "observation_count": int(state.observation_count) if state else 0,
        "proficiency_claim": "instructional_estimate_not_certification",
    }


def get_user_competency_profile(db: Session, *, user_id, language_code: str) -> dict:
    skills = ensure_catalog(db, language_code)
    state_by_skill = {
        state.skill_id: state for state in db.query(LearnerSkillState).filter(
            LearnerSkillState.user_id == user_id,
            LearnerSkillState.skill_id.in_([skill.id for skill in skills]),
        ).all()
    }
    entries = []
    observed_modalities = set()
    qualified_levels = []
    level_order = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
    for skill in skills:
        state = state_by_skill.get(skill.id)
        count = int(state.observation_count) if state else 0
        mastery = float(state.mastery_probability) if state else 0.5
        if count >= 3:
            observed_modalities.add(skill.modality)
            if mastery >= 0.72:
                qualified_levels.append(skill.framework_level)
        entries.append({
            "code": skill.code,
            "name": skill.name,
            "framework_level": skill.framework_level,
            "modality": skill.modality,
            "can_do_descriptor": skill.can_do_descriptor,
            "mastery_probability": mastery,
            "confidence": float(state.confidence) if state else 0.0,
            "observation_count": count,
            "independent_success_rate": float(state.independent_success_rate) if state else 0.0,
            "next_practice_at": state.next_practice_at if state else None,
        })
    assessed = [entry for entry in entries if entry["observation_count"] >= 3]
    enough_evidence = bool(len(assessed) >= 4 and len(observed_modalities) >= 2 and qualified_levels)
    return {
        "language_code": language_code,
        "catalog_version": CATALOG_VERSION,
        "instructional_band": max(qualified_levels, key=lambda level: level_order.get(level, 0)) if enough_evidence else None,
        "assessment_basis": "multi_skill_observation" if enough_evidence else "insufficient_cross_skill_evidence",
        "certification_claim": False,
        "skills": entries,
    }
