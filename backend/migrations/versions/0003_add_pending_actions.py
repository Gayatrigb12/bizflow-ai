"""add pending_actions table for AI approval workflow

Revision ID: 0003_add_pending_actions
Revises: 0002_add_knowledge_embeddings
Create Date: 2026-06-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_add_pending_actions'
down_revision = '0002_add_knowledge_embeddings'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'pending_actions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('action_type', sa.String(length=80), nullable=False),
        sa.Column('payload', sa.JSON, nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('requested_by', sa.String(length=128), nullable=True),
        sa.Column('reviewed_by', sa.String(length=128), nullable=True),
        sa.Column('review_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_table('pending_actions')
