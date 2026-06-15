from typing import Dict, Any

from backend.embeddings.embedding_service import generate_embedding
from backend.embeddings.retriever import similarity_search
from backend.services.report_service import ReportService
from backend.storage.models import Customer, Order, Product


class ContextBuilder:
    def __init__(self, session):
        self.session = session

    def build(self, query: str = '') -> Dict[str, Any]:
        state = ReportService(self.session).build_dashboard_state()
        if query and query.strip():
            query_embedding = generate_embedding(query)
            matches = similarity_search(self.session, query_embedding, top_k=4)
            state['retrieval_snippets'] = [self._build_retrieval_entry(match) for match in matches]
        else:
            state['retrieval_snippets'] = []
        return state

    def _build_retrieval_entry(self, match: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'object_type': match['object_type'],
            'object_id': match['object_id'],
            'metadata': match.get('metadata') or {},
            'distance': match.get('distance'),
            'snippet': self._render_snippet(match),
        }

    def _render_snippet(self, match: Dict[str, Any]) -> str:
        object_type = match.get('object_type')
        object_id = match.get('object_id')
        metadata = match.get('metadata') or {}

        if object_type == 'product':
            product = self.session.get(Product, object_id)
            if product:
                return self._render_product_text(product)
            return self._render_product_metadata(metadata)

        if object_type == 'customer':
            customer = self.session.get(Customer, object_id)
            if customer:
                return self._render_customer_text(customer)
            return self._render_customer_metadata(metadata)

        if object_type == 'order':
            order = self.session.get(Order, object_id)
            if order:
                return self._render_order_text(order)
            return self._render_order_metadata(metadata)

        return str(metadata or f'{object_type}:{object_id}')

    def _render_product_text(self, product: Product) -> str:
        fields = [product.name, f'SKU {product.sku}' if product.sku else None, f'price ₹{product.price}', f'qty {product.quantity}', product.description]
        return ' | '.join([part for part in fields if part])

    def _render_customer_text(self, customer: Customer) -> str:
        fields = [customer.name, customer.email, customer.phone, customer.address]
        return ' | '.join([part for part in fields if part])

    def _render_order_text(self, order: Order) -> str:
        parts = [f'Invoice {order.invoice_number}', f'Customer {order.customer.name if order.customer else order.customer_id}', f'Status {order.status}', f'Total ₹{order.total}']
        item_lines = []
        for item in getattr(order, 'items', []) or []:
            item_lines.append(f'{item.quantity}x {item.product.name if item.product else item.product_id} @ ₹{item.unit_price}')
        if item_lines:
            parts.append('Items: ' + '; '.join(item_lines))
        return ' | '.join(parts)

    @staticmethod
    def _render_product_metadata(metadata: Dict[str, Any]) -> str:
        return ' | '.join([str(metadata.get(key)) for key in ('name', 'sku', 'price', 'quantity') if metadata.get(key) is not None])

    @staticmethod
    def _render_customer_metadata(metadata: Dict[str, Any]) -> str:
        return ' | '.join([str(metadata.get(key)) for key in ('name', 'email', 'phone', 'address') if metadata.get(key)])

    @staticmethod
    def _render_order_metadata(metadata: Dict[str, Any]) -> str:
        return ' | '.join([str(metadata.get(key)) for key in ('invoice_number', 'customer_id', 'status', 'total') if metadata.get(key)])
