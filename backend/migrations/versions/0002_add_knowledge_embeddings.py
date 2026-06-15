"""add knowledge_embeddings table and pgvector extension

Revision ID: 0002_add_knowledge_embeddings
Revises: 0001_create_initial_tables
Create Date: 2026-06-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = '0002_add_knowledge_embeddings'
down_revision = '0001_create_initial_tables'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    vector_type = sa.JSON

    try:
        bind.execute(sa.text('CREATE EXTENSION IF NOT EXISTS vector'))
        from pgvector.sqlalchemy import Vector
        vector_type = Vector(1536)
    except Exception:
        vector_type = sa.JSON

    if 'knowledge_embeddings' not in inspect(bind).get_table_names():
        op.create_table(
            'knowledge_embeddings',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('object_type', sa.String(length=80), nullable=False),
            sa.Column('object_id', sa.Integer, nullable=False),
            sa.Column('embedding', vector_type, nullable=False),
            sa.Column('metadata', sa.JSON, nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )


def downgrade():
    op.drop_table('knowledge_embeddings')
