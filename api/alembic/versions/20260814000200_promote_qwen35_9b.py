"""promote Qwen3.5 9B as the local LLM default

Revision ID: 20260814000200
Revises: 20260814000100
Create Date: 2026-08-14 00:02:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260814000200"
down_revision = "20260814000100"
branch_labels = None
depends_on = None


NEW_PROFILE = "qwen3.5-9b"
PREVIOUS_PROFILE = "qwen2.5-7b-instruct"


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE user_llm_preferences "
            "SET chat_model_profile = :new_profile "
            "WHERE chat_model_profile IN (:previous_profile, 'gemma-4-e4b-it')"
        ).bindparams(new_profile=NEW_PROFILE, previous_profile=PREVIOUS_PROFILE)
    )
    op.execute(
        sa.text(
            "UPDATE user_llm_preferences "
            "SET teacher_model_profile = :new_profile "
            "WHERE teacher_model_profile IN (:previous_profile, 'gemma-4-e4b-it')"
        ).bindparams(new_profile=NEW_PROFILE, previous_profile=PREVIOUS_PROFILE)
    )
    op.alter_column(
        "user_llm_preferences",
        "chat_model_profile",
        server_default=NEW_PROFILE,
        existing_type=sa.String(length=100),
        existing_nullable=False,
    )
    op.alter_column(
        "user_llm_preferences",
        "teacher_model_profile",
        server_default=NEW_PROFILE,
        existing_type=sa.String(length=100),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE user_llm_preferences "
            "SET chat_model_profile = :previous_profile "
            "WHERE chat_model_profile = :new_profile"
        ).bindparams(new_profile=NEW_PROFILE, previous_profile=PREVIOUS_PROFILE)
    )
    op.execute(
        sa.text(
            "UPDATE user_llm_preferences "
            "SET teacher_model_profile = :previous_profile "
            "WHERE teacher_model_profile = :new_profile"
        ).bindparams(new_profile=NEW_PROFILE, previous_profile=PREVIOUS_PROFILE)
    )
    op.alter_column(
        "user_llm_preferences",
        "chat_model_profile",
        server_default=PREVIOUS_PROFILE,
        existing_type=sa.String(length=100),
        existing_nullable=False,
    )
    op.alter_column(
        "user_llm_preferences",
        "teacher_model_profile",
        server_default=PREVIOUS_PROFILE,
        existing_type=sa.String(length=100),
        existing_nullable=False,
    )
