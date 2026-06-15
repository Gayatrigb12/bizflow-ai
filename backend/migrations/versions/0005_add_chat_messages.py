"""add chat_messages table for AI chat persistence with module context

Revision ID: 0005_add_chat_messages
Revises: 0004_add_refresh_token_hash
Create Date: 2026-06-12 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0005_add_chat_messages'
down_revision = '0004_add_refresh_token_hash'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('context_type', sa.String(length=32), nullable=False, server_default='general'),
        sa.Column('context_id', sa.Integer, nullable=True),
        sa.Column('role', sa.String(length=16), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('actions', sa.JSON(), nullable=True),
        sa.Column('actor', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_chat_messages_context_type', 'chat_messages', ['context_type'])
    op.create_index('ix_chat_messages_created_at', 'chat_messages', ['created_at'])


def downgrade():
    op.drop_index('ix_chat_messages_created_at', table_name='chat_messages')
    op.drop_index('ix_chat_messages_context_type', table_name='chat_messages')
    op.drop_table('chat_messages')
