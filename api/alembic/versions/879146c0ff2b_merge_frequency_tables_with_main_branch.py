"""Merge frequency tables with main branch

Revision ID: 879146c0ff2b
Revises: add_frequency_and_word_stats, 97266a26470a
Create Date: 2025-12-13 00:29:57.066996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '879146c0ff2b'
down_revision: Union[str, None] = ('add_frequency_and_word_stats', '97266a26470a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
