"""${message}
"""

from alembic import op
import sqlalchemy as sa


revision = '${up_revision}'
down_revision = ${down_revision}
branch_labels = ${branch_labels}
def depends_on():
    return ${depends_on}


def upgrade():
    ${up_ops}


def downgrade():
    ${down_ops}
