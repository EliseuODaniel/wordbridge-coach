"""add competency learning core and FSRS shadow state

Revision ID: 20260814000100
Revises: 20251226150000
Create Date: 2026-08-14 00:01:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260814000100"
down_revision = "20251226150000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learning_skill",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("code", sa.String(120), nullable=False),
        sa.Column("language_code", sa.String(8), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.String(1000), nullable=False),
        sa.Column("framework", sa.String(40), nullable=False, server_default="CEFR"),
        sa.Column("framework_level", sa.String(16), nullable=False),
        sa.Column("modality", sa.String(32), nullable=False),
        sa.Column("can_do_descriptor", sa.String(1000), nullable=False),
        sa.Column("concept_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("catalog_version", sa.String(40), nullable=False, server_default="en-core-v1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_learning_skill_code", "learning_skill", ["code"], unique=True)
    op.create_index("ix_learning_skill_language_code", "learning_skill", ["language_code"])

    op.create_table(
        "sentence_skill",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("sentence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(24), nullable=False, server_default="primary"),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1"),
        sa.Column("mapping_source", sa.String(40), nullable=False, server_default="catalog_heuristic_v1"),
        sa.ForeignKeyConstraint(["sentence_id"], ["sentence.id"]),
        sa.ForeignKeyConstraint(["skill_id"], ["learning_skill.id"]),
        sa.UniqueConstraint("sentence_id", "skill_id", name="uq_sentence_skill"),
    )
    op.create_index("ix_sentence_skill_sentence_id", "sentence_skill", ["sentence_id"])
    op.create_index("ix_sentence_skill_skill_id", "sentence_skill", ["skill_id"])

    op.create_table(
        "learner_skill_state",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_weight", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence_weight", sa.Float(), nullable=False, server_default="0"),
        sa.Column("mastery_probability", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("independent_success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("independent_attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("independent_success_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_observed_at", sa.DateTime(), nullable=True),
        sa.Column("next_practice_at", sa.DateTime(), nullable=True),
        sa.Column("model_version", sa.String(40), nullable=False, server_default="beta-evidence-v1"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["skill_id"], ["learning_skill.id"]),
        sa.UniqueConstraint("user_id", "skill_id", name="uq_learner_skill_state"),
    )
    op.create_index("ix_learner_skill_state_user_id", "learner_skill_state", ["user_id"])
    op.create_index("ix_learner_skill_state_skill_id", "learner_skill_state", ["skill_id"])

    op.create_table(
        "pedagogical_observation",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("card_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sentence_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("mode", sa.String(24), nullable=False),
        sa.Column("task_type", sa.String(40), nullable=False),
        sa.Column("modality", sa.String(32), nullable=False),
        sa.Column("was_correct", sa.Boolean(), nullable=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("hints_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("scaffold_level", sa.String(24), nullable=False, server_default="independent"),
        sa.Column("was_independent", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("learner_answer", sa.String(2000), nullable=True),
        sa.Column("policy_version", sa.String(40), nullable=False, server_default="pedagogy-policy-v1"),
        sa.Column("model_version", sa.String(40), nullable=False, server_default="beta-evidence-v1"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["skill_id"], ["learning_skill.id"]),
        sa.ForeignKeyConstraint(["card_id"], ["card.id"]),
        sa.ForeignKeyConstraint(["sentence_id"], ["sentence.id"]),
    )
    op.create_index("ix_pedagogical_observation_user_id", "pedagogical_observation", ["user_id"])
    op.create_index("ix_pedagogical_observation_skill_id", "pedagogical_observation", ["skill_id"])
    op.create_index("ix_pedagogical_observation_card_id", "pedagogical_observation", ["card_id"])
    op.create_index("ix_pedagogical_observation_session_id", "pedagogical_observation", ["session_id"])

    sentence_columns = (
        ("cefr_level", sa.String(16), None),
        ("register", sa.String(32), "neutral"),
        ("domain", sa.String(64), None),
        ("competency_codes", postgresql.JSONB(astext_type=sa.Text()), sa.text("'[]'::jsonb")),
        ("grammar_tags", postgresql.JSONB(astext_type=sa.Text()), sa.text("'[]'::jsonb")),
        ("quality_status", sa.String(24), "unreviewed"),
        ("license_name", sa.String(120), None),
        ("content_version", sa.String(40), "legacy-v1"),
        ("is_contemporary", sa.Boolean(), sa.false()),
    )
    for name, column_type, default in sentence_columns:
        nullable = default is None
        op.add_column("sentence", sa.Column(name, column_type, nullable=nullable, server_default=default))
    op.execute(
        "UPDATE sentence SET quality_status = 'literary', "
        "license_name = 'Public Domain', content_version = 'gutenberg-literary-v1' "
        "WHERE source_ref LIKE 'gutenberg:%'"
    )
    op.execute(
        "UPDATE sentence SET quality_status = 'needs_review', "
        "content_version = 'legacy-generated-v1' WHERE source_ref IS NULL"
    )
    op.execute(
        "UPDATE sentence SET gap_start = strpos(text, '___') - 1, "
        "gap_end = strpos(text, '___') + 2 WHERE strpos(text, '___') > 0"
    )
    op.execute(
        "UPDATE card SET gap_start = sentence.gap_start, gap_end = sentence.gap_end "
        "FROM sentence WHERE card.sentence_id = sentence.id AND strpos(sentence.text, '___') > 0"
    )

    state_columns = (
        ("fsrs_card_json", postgresql.JSONB(astext_type=sa.Text())),
        ("fsrs_last_retrievability", sa.Float()),
        ("fsrs_next_review_at", sa.DateTime()),
        ("fsrs_interval_days", sa.Float()),
        ("scheduler_shadow_version", sa.String(40)),
    )
    for name, column_type in state_columns:
        op.add_column("usercardstate", sa.Column(name, column_type, nullable=True))

    review_columns = (
        ("mode", sa.String(24), "spec4", False),
        ("task_type", sa.String(40), "gap_recall", False),
        ("modality", sa.String(32), "reading_writing", False),
        ("scaffold_level", sa.String(24), "independent", False),
        ("was_independent", sa.Boolean(), sa.true(), False),
        ("policy_version", sa.String(40), "pedagogy-policy-v1", False),
        ("scheduler_shadow_version", sa.String(40), None, True),
        ("fsrs_predicted_recall", sa.Float(), None, True),
        ("fsrs_next_review_at", sa.DateTime(), None, True),
        ("fsrs_interval_days", sa.Float(), None, True),
        ("fsrs_review_log_json", postgresql.JSONB(astext_type=sa.Text()), None, True),
    )
    for name, column_type, default, nullable in review_columns:
        op.add_column("reviewevent", sa.Column(name, column_type, nullable=nullable, server_default=default))


def downgrade() -> None:
    for name in (
        "fsrs_review_log_json", "fsrs_interval_days", "fsrs_next_review_at",
        "fsrs_predicted_recall", "scheduler_shadow_version", "policy_version",
        "was_independent", "scaffold_level", "modality", "task_type", "mode",
    ):
        op.drop_column("reviewevent", name)
    for name in (
        "scheduler_shadow_version", "fsrs_interval_days", "fsrs_next_review_at",
        "fsrs_last_retrievability", "fsrs_card_json",
    ):
        op.drop_column("usercardstate", name)
    for name in (
        "is_contemporary", "content_version", "license_name", "quality_status",
        "grammar_tags", "competency_codes", "domain", "register", "cefr_level",
    ):
        op.drop_column("sentence", name)
    op.drop_table("pedagogical_observation")
    op.drop_table("learner_skill_state")
    op.drop_table("sentence_skill")
    op.drop_table("learning_skill")
