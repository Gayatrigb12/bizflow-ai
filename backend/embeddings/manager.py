from typing import Optional

from backend.embeddings.embedding_service import generate_embedding
from backend.embeddings.vector_store import upsert_embedding
from backend.storage.models import Customer, Order, OrderItem, Product


def _render_product_text(product: Product) -> str:
    parts = [product.name, product.description or '']
    if product.sku:
        parts.append(f"SKU {product.sku}")
    parts.append(f"price {product.price}")
    parts.append(f"qty {product.quantity}")
    return ' | '.join(p.strip() for p in parts if p)


def _render_customer_text(customer: Customer) -> str:
    parts = [customer.name, customer.email or '', customer.phone or '', customer.address or '']
    return ' | '.join(p.strip() for p in parts if p)


def _render_order_text(order: Order) -> str:
    parts = [
        f"Invoice {order.invoice_number}",
        f"Customer {order.customer.name if order.customer else order.customer_id}",
        f"Status {order.status}",
        f"Total {order.total}",
    ]
    item_lines = []
    for item in order.items:
        item_lines.append(f"{item.quantity}x {item.product.name if item.product else item.product_id} @ {item.unit_price}")
    if item_lines:
        parts.append('Items: ' + '; '.join(item_lines))
    return ' | '.join(parts)


def index_product_embedding(session, product: Product) -> bool:
    text = _render_product_text(product)
    embedding = generate_embedding(text)
    metadata = {
        'type': 'product',
        'name': product.name,
        'sku': product.sku,
        'price': product.price,
        'quantity': product.quantity,
    }
    return upsert_embedding(session, 'product', product.id, embedding, metadata)


def index_customer_embedding(session, customer: Customer) -> bool:
    text = _render_customer_text(customer)
    embedding = generate_embedding(text)
    metadata = {
        'type': 'customer',
        'name': customer.name,
        'email': customer.email,
        'phone': customer.phone,
    }
    return upsert_embedding(session, 'customer', customer.id, embedding, metadata)


def index_order_embedding(session, order: Order) -> bool:
    text = _render_order_text(order)
    embedding = generate_embedding(text)
    metadata = {
        'type': 'order',
        'invoice_number': order.invoice_number,
        'customer_id': order.customer_id,
        'total': order.total,
    }
    return upsert_embedding(session, 'order', order.id, embedding, metadata)


def index_entity_embedding(session, object_type: str, object_id: int, text: str, metadata: Optional[dict] = None) -> bool:
    embedding = generate_embedding(text)
    return upsert_embedding(session, object_type, object_id, embedding, metadata or {})
