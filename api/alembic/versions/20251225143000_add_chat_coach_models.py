"""add chat coach models

Revision ID: 20251225143000
Revises: 20251225014903
Create Date: 2025-12-25 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '20251225143000'
down_revision = '20251225014903'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create chat_conversations table
    op.create_table(
        'chat_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False, server_default='New Chat'),
        sa.Column('student_profile_json', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('lesson_frame_json', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('session_summary', sa.Text(), nullable=False, server_default=''),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_chat_conversations_user_id'),
    )
    op.create_index('ix_chat_conversations_user_id', 'chat_conversations', ['user_id'])
    op.create_index('ix_chat_conversations_created_at', 'chat_conversations', [sa.text('created_at DESC')])

    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversations.id'], ondelete='CASCADE', name='fk_chat_messages_conversation_id'),
    )
    op.create_index('ix_chat_messages_conversation_id', 'chat_messages', ['conversation_id'])
    op.create_index('ix_chat_messages_created_at', 'chat_messages', [sa.text('created_at ASC')])

    # Create chat_lesson_history table (optional, Phase 2)
    op.create_table(
        'chat_lesson_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lesson_frame_json', postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['chat_conversations.id'], ondelete='CASCADE', name='fk_chat_lesson_history_conversation_id'),
    )
    op.create_index('ix_chat_lesson_history_conversation_id', 'chat_lesson_history', ['conversation_id'])


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_index('ix_chat_lesson_history_conversation_id', table_name='chat_lesson_history')
    op.drop_table('chat_lesson_history')

    op.drop_index('ix_chat_messages_created_at', table_name='chat_messages')
    op.drop_index('ix_chat_messages_conversation_id', table_name='chat_messages')
    op.drop_table('chat_messages')

    op.drop_index('ix_chat_conversations_created_at', table_name='chat_conversations')
    op.drop_index('ix_chat_conversations_user_id', table_name='chat_conversations')
    op.drop_table('chat_conversations')
