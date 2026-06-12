"""Create initial BizFlow AI tables
"""

from alembic import op
import sqlalchemy as sa

revision = '0001_create_initial_tables'
down_revision = None
branch_labels = None
depend_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(length=128), nullable=False, unique=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=64), nullable=False, server_default='staff'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'customers',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=64), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('total_spent', sa.Float, nullable=False, server_default='0'),
        sa.Column('order_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'products',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('sku', sa.String(length=64), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('unit', sa.String(length=64), nullable=False, server_default='pcs'),
        sa.Column('price', sa.Float, nullable=False, server_default='0'),
        sa.Column('quantity', sa.Float, nullable=False, server_default='0'),
        sa.Column('low_stock_threshold', sa.Float, nullable=False, server_default='10'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'orders',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('invoice_number', sa.String(length=128), nullable=False, unique=True),
        sa.Column('customer_id', sa.Integer, sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('subtotal', sa.Float, nullable=False, server_default='0'),
        sa.Column('tax', sa.Float, nullable=False, server_default='0'),
        sa.Column('total', sa.Float, nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=64), nullable=False, server_default='draft'),
        sa.Column('payment_status', sa.String(length=64), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('order_id', sa.Integer, sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('product_id', sa.Integer, sa.ForeignKey('products.id'), nullable=True),
        sa.Column('quantity', sa.Float, nullable=False, server_default='0'),
        sa.Column('unit_price', sa.Float, nullable=False, server_default='0'),
        sa.Column('line_total', sa.Float, nullable=False, server_default='0'),
    )

    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('action_type', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('actor', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table('activity_logs')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('products')
    op.drop_table('customers')
    op.drop_table('users')
