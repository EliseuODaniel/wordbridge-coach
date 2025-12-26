"""add adaptive scheduler fields

Revision ID: 20251225014903
Revises: add_lingvist_fields
Create Date: 2025-12-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20251225014903'
down_revision = 'add_lingvist_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add fields to User table
    op.add_column('user', sa.Column('mode', sa.String(20), nullable=False, server_default='spec4'))
    op.add_column('user', sa.Column('accuracy_last_20', sa.Float(), nullable=True))

    # Add fields to UserCardState table
    op.add_column('usercardstate', sa.Column('is_relearn', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('usercardstate', sa.Column('relearn_due', sa.DateTime(), nullable=True))

    # Add attempts field to ReviewEvent (hints_used_lingvist already exists)
    op.add_column('reviewevent', sa.Column('attempts', sa.Integer(), nullable=False, server_default='1'))

    # Create indexes for performance
    # Partial index for relearn cards (only indexes where is_relearn = true)
    op.create_index(
        'idx_user_card_relearn',
        'usercardstate',
        ['user_id', 'is_relearn', 'relearn_due'],
        unique=False,
        postgresql_where=sa.text('is_relearn = TRUE')
    )

    # Index for user accuracy lookups
    op.create_index(
        'idx_user_accuracy',
        'user',
        ['id', 'accuracy_last_20'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_user_accuracy', table_name='user')
    op.drop_index('idx_user_card_relearn', table_name='usercardstate')

    # Remove fields from ReviewEvent
    op.drop_column('reviewevent', 'attempts')

    # Remove fields from UserCardState
    op.drop_column('usercardstate', 'relearn_due')
    op.drop_column('usercardstate', 'is_relearn')

    # Remove fields from User
    op.drop_column('user', 'accuracy_last_20')
    op.drop_column('user', 'mode')
