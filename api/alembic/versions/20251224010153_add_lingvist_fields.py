"""add lingvist fields to review_event

Revision ID: add_lingvist_fields
Revises:
Create Date: 2025-12-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_lingvist_fields'
down_revision = 'e6bebc24dc86'  # After add_sentence_source_fields
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Lingvist mode tracking fields to ReviewEvent
    # All nullable to not break Spec4 mode

    op.add_column('reviewevent', sa.Column('typed_answer', sa.String(200), nullable=True))
    op.add_column('reviewevent', sa.Column('hints_used_lingvist', sa.JSON(), nullable=True))
    op.add_column('reviewevent', sa.Column('attempt_index', sa.Integer(), nullable=True))

    # Note: word_translation_pt will use Word.features.pt_translation (JSON field)
    # No new column needed on Word table


def downgrade() -> None:
    # Remove Lingvist fields from ReviewEvent
    op.drop_column('reviewevent', 'attempt_index')
    op.drop_column('reviewevent', 'hints_used_lingvist')
    op.drop_column('reviewevent', 'typed_answer')
