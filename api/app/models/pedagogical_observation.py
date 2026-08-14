"""Normalized evidence emitted by objectively scored learning activities."""

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class PedagogicalObservation(BaseModel):
    __tablename__ = "pedagogical_observation"

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("learning_skill.id"), nullable=True, index=True)
    card_id = Column(UUID(as_uuid=True), ForeignKey("card.id"), nullable=True, index=True)
    sentence_id = Column(UUID(as_uuid=True), ForeignKey("sentence.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    event_type = Column(String(40), nullable=False)
    mode = Column(String(24), nullable=False)
    task_type = Column(String(40), nullable=False)
    modality = Column(String(32), nullable=False)
    was_correct = Column(Boolean, nullable=True)
    score = Column(Float, nullable=False)
    hints_used = Column(Integer, nullable=False, default=0)
    attempts = Column(Integer, nullable=False, default=1)
    response_time_ms = Column(Integer, nullable=True)
    scaffold_level = Column(String(24), nullable=False, default="independent")
    was_independent = Column(Boolean, nullable=False, default=True)
    learner_answer = Column(String(2000), nullable=True)
    policy_version = Column(String(40), nullable=False, default="pedagogy-policy-v1")
    model_version = Column(String(40), nullable=False, default="beta-evidence-v1")
    metadata_json = Column(JSON, nullable=False, default=dict)
