"""Mapping between a sentence item and the competencies it elicits."""

from sqlalchemy import Column, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class SentenceSkill(BaseModel):
    __tablename__ = "sentence_skill"
    __table_args__ = (
        UniqueConstraint("sentence_id", "skill_id", name="uq_sentence_skill"),
    )

    sentence_id = Column(UUID(as_uuid=True), ForeignKey("sentence.id"), nullable=False, index=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("learning_skill.id"), nullable=False, index=True)
    role = Column(String(24), nullable=False, default="primary")
    weight = Column(Float, nullable=False, default=1.0)
    mapping_source = Column(String(40), nullable=False, default="catalog_heuristic_v1")
