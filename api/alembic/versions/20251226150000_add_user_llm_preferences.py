"""add user llm preferences

Revision ID: 20251226150000
Revises: 20251225143000
Create Date: 2025-12-26 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20251226150000'
down_revision = '20251225143000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_llm_preferences table
    op.create_table(
        'user_llm_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chat_model_profile', sa.String(100), nullable=False, server_default='qwen2.5-7b-instruct'),
        sa.Column('teacher_model_profile', sa.String(100), nullable=False, server_default='qwen2.5-7b-instruct'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_user_llm_preferences_user_id'),
    )
    op.create_index('ix_user_llm_preferences_user_id', 'user_llm_preferences', ['user_id'], unique=True)


def downgrade() -> None:
    # Drop table
    op.drop_index('ix_user_llm_preferences_user_id', table_name='user_llm_preferences')
    op.drop_table('user_llm_preferences')
