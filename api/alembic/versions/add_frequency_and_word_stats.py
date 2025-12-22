"""Add word_frequency and user_word_stats tables

Revision ID: add_frequency_and_word_stats
Revises: 2a3b4c5d6e7f
Create Date: 2025-12-12 21:29:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_frequency_and_word_stats'
down_revision: Union[str, None] = '2a3b4c5d6e7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create word_frequencies table
    op.create_table('word_frequencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('word', sa.String(length=100), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('frequency_score', sa.Float(), nullable=True),
        sa.Column('band', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_word_frequency_word', 'word_frequencies', ['word'], unique=False)
    op.create_index('idx_word_frequency_rank', 'word_frequencies', ['rank'], unique=False)
    op.create_index('idx_word_frequency_band', 'word_frequencies', ['band'], unique=False)
    op.create_index('idx_word_frequency_active_band', 'word_frequencies', ['is_active', 'band'], unique=False)

    # Create user_word_stats table
    op.create_table('user_word_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('word_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_attempts', sa.Integer(), nullable=False),
        sa.Column('correct_attempts', sa.Integer(), nullable=False),
        sa.Column('accuracy_rate', sa.Float(), nullable=False),
        sa.Column('mastery_score', sa.Float(), nullable=False),
        sa.Column('last_result', sa.Boolean(), nullable=True),
        sa.Column('consecutive_correct', sa.Integer(), nullable=False),
        sa.Column('consecutive_incorrect', sa.Integer(), nullable=False),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['word_id'], ['word.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_word_stats_user_word', 'user_word_stats', ['user_id', 'word_id'], unique=True)
    op.create_index('idx_user_word_stats_user_mastery', 'user_word_stats', ['user_id', 'mastery_score'], unique=False)
    op.create_index('idx_user_word_stats_user_accuracy', 'user_word_stats', ['user_id', 'accuracy_rate'], unique=False)


def downgrade() -> None:
    op.drop_table('user_word_stats')
    op.drop_table('word_frequencies')