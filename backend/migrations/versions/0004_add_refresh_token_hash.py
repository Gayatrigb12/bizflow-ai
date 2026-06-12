"""Add refresh token hash to users

Revision ID: 0004_add_refresh_token_hash
Revises: 0003_add_pending_actions
Create Date: 2026-06-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0004_add_refresh_token_hash'
down_revision = '0003_add_pending_actions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('refresh_token_hash', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'refresh_token_hash')
