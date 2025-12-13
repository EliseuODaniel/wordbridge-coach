"""Fix user language columns to use UUID instead of string

Revision ID: fix_user_language_cols
Revises: 870c67fe87be
Create Date: 2025-12-12 04:18:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_user_language_cols'
down_revision = '870c67fe87be'
branch_labels = None
depends_on = None


def upgrade():
    # Add new UUID columns
    op.add_column('user', sa.Column('native_language_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('user', sa.Column('target_language_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Populate new columns with data from language table
    op.execute("""
        UPDATE "user"
        SET native_language_id = language.id
        FROM language
        WHERE language.code = "user".native_language
    """)

    op.execute("""
        UPDATE "user"
        SET target_language_id = language.id
        FROM language
        WHERE language.code = "user".target_language
    """)

    # Make new columns not nullable
    op.alter_column('user', 'native_language_id', nullable=False)
    op.alter_column('user', 'target_language_id', nullable=False)

    # Drop old columns
    op.drop_column('user', 'native_language')
    op.drop_column('user', 'target_language')


def downgrade():
    # Add old string columns back
    op.add_column('user', sa.Column('native_language', sa.String(length=10), nullable=True))
    op.add_column('user', sa.Column('target_language', sa.String(length=10), nullable=True))

    # Populate old columns with data from language table
    op.execute("""
        UPDATE "user"
        SET native_language = language.code
        FROM language
        WHERE language.id = "user".native_language_id
    """)

    op.execute("""
        UPDATE "user"
        SET target_language = language.code
        FROM language
        WHERE language.id = "user".target_language_id
    """)

    # Drop new UUID columns
    op.drop_column('user', 'target_language_id')
    op.drop_column('user', 'native_language_id')