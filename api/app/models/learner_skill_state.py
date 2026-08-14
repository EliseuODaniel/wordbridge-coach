"""Per-learner evidence state for an explicit language competency."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class LearnerSkillState(BaseModel):
    __tablename__ = "learner_skill_state"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_learner_skill_state"),
    )

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("learning_skill.id"), nullable=False, index=True)
    observation_count = Column(Integer, nullable=False, default=0)
    success_weight = Column(Float, nullable=False, default=0.0)
    evidence_weight = Column(Float, nullable=False, default=0.0)
    mastery_probability = Column(Float, nullable=False, default=0.5)
    confidence = Column(Float, nullable=False, default=0.0)
    independent_success_count = Column(Integer, nullable=False, default=0)
    independent_attempt_count = Column(Integer, nullable=False, default=0)
    independent_success_rate = Column(Float, nullable=False, default=0.0)
    last_observed_at = Column(DateTime, nullable=True)
    next_practice_at = Column(DateTime, nullable=True)
    model_version = Column(String(40), nullable=False, default="beta-evidence-v1")
