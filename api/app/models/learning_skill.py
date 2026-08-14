"""Explicit language-learning competency model."""

from sqlalchemy import Boolean, Column, JSON, String

from app.models.base import BaseModel


class LearningSkill(BaseModel):
    """A versioned CEFR/ACTFL-aligned capability used across study modes."""

    __tablename__ = "learning_skill"

    code = Column(String(120), unique=True, nullable=False, index=True)
    language_code = Column(String(8), nullable=False, index=True)
    name = Column(String(160), nullable=False)
    description = Column(String(1000), nullable=False)
    framework = Column(String(40), nullable=False, default="CEFR")
    framework_level = Column(String(16), nullable=False)
    modality = Column(String(32), nullable=False)
    can_do_descriptor = Column(String(1000), nullable=False)
    concept_tags = Column(JSON, nullable=False, default=list)
    catalog_version = Column(String(40), nullable=False, default="en-core-v1")
    is_active = Column(Boolean, nullable=False, default=True)
