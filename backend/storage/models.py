from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from backend.storage.database import Base, is_sqlite, pgvector_enabled


def utc_now() -> datetime:
    return datetime.utcnow()


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(64), unique=True, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    unit = Column(String(64), nullable=False, default='pcs')
    price = Column(Float, nullable=False, default=0.0)
    quantity = Column(Float, nullable=False, default=0.0)
    low_stock_threshold = Column(Float, nullable=False, default=10.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    order_items = relationship('OrderItem', back_populates='product')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'unit': self.unit,
            'price': self.price,
            'quantity': self.quantity,
            'low_stock_threshold': self.low_stock_threshold,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    phone = Column(String(64), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    total_spent = Column(Float, nullable=False, default=0.0)
    order_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    orders = relationship('Order', back_populates='customer')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'total_spent': self.total_spent,
            'order_count': self.order_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(128), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    subtotal = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    status = Column(String(64), nullable=False, default='draft')
    payment_status = Column(String(64), nullable=False, default='pending')
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    customer = relationship('Customer', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'customer_id': self.customer_id,
            'customer': self.customer.name if self.customer else None,
            'subtotal': self.subtotal,
            'tax': self.tax,
            'total': self.total,
            'status': self.status,
            'payment_status': self.payment_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'items': [item.to_dict() for item in self.items],
        }


class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    quantity = Column(Float, nullable=False, default=0.0)
    unit_price = Column(Float, nullable=False, default=0.0)
    line_total = Column(Float, nullable=False, default=0.0)

    order = relationship('Order', back_populates='items')
    product = relationship('Product', back_populates='order_items')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'name': self.product.name if self.product else None,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'line_total': self.line_total,
        }


class ActivityLog(Base):
    __tablename__ = 'activity_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    actor = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'action_type': self.action_type,
            'description': self.description,
            'actor': self.actor,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(128), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    refresh_token_hash = Column(String(255), nullable=True)
    role = Column(String(64), nullable=False, default='staff')
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# KnowledgeEmbedding: stores vector embeddings for RAG and similarity search.
try:
    from pgvector.sqlalchemy import Vector
except Exception:
    Vector = None

class KnowledgeEmbedding(Base):
    __tablename__ = 'knowledge_embeddings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    object_type = Column(String(80), nullable=False)  # e.g., 'product', 'customer', 'order'
    object_id = Column(Integer, nullable=False)
    # Use pgvector Vector only when running against PostgreSQL; fall back to JSON on SQLite.
    if Vector is not None and pgvector_enabled():
        embedding = Column(Vector(1536), nullable=False)
    else:
        embedding = Column(JSON, nullable=False)
    # attribute name `metadata` is reserved by SQLAlchemy declarative; use `meta` mapped to DB column `metadata`
    meta = Column('metadata', JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'object_type': self.object_type,
            'object_id': self.object_id,
            'embedding': self.embedding,
            'metadata': self.meta,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class PendingAction(Base):
    __tablename__ = 'pending_actions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String(80), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(32), nullable=False, default='pending')
    requested_by = Column(String(128), nullable=True)
    reviewed_by = Column(String(128), nullable=True)
    review_comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'action_type': self.action_type,
            'payload': self.payload,
            'status': self.status,
            'requested_by': self.requested_by,
            'reviewed_by': self.reviewed_by,
            'review_comment': self.review_comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_prompt = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    context_type = Column(String(64), nullable=True)
    entity_type = Column(String(64), nullable=True)
    entity_id = Column(Integer, nullable=True)
    actor = Column(String(128), nullable=True)
    session_id = Column(String(128), nullable=True)
    metadata_json = Column('metadata', JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_prompt': self.user_prompt,
            'ai_response': self.ai_response,
            'context_type': self.context_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'actor': self.actor,
            'session_id': self.session_id,
            'metadata': self.metadata_json,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
