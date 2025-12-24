"""add sentence source fields

Revision ID: e6bebc24dc86
Revises: add_spec4_models
Create Date: 2025-12-24 00:57:36.295220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6bebc24dc86'
down_revision: Union[str, None] = 'add_spec4_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add source metadata columns to sentence table
    op.add_column('sentence', sa.Column('source_title', sa.String(200), nullable=True))
    op.add_column('sentence', sa.Column('source_author', sa.String(200), nullable=True))
    op.add_column('sentence', sa.Column('source_ref', sa.String(50), nullable=True))


def downgrade() -> None:
    # Remove source metadata columns from sentence table
    op.drop_column('sentence', 'source_ref')
    op.drop_column('sentence', 'source_author')
    op.drop_column('sentence', 'source_title')
