from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.embeddings.manager import index_order_embedding
from backend.storage.models import Order, OrderItem
from backend.storage.repositories.order_repository import OrderRepository
from backend.services.customer_service import CustomerService
from backend.services.inventory_service import InventoryService


class OrderService:
    def __init__(self, session):
        self.session = session
        self.repository = OrderRepository(session)
        self.inventory_service = InventoryService(session)
        self.customer_service = CustomerService(session)

    def list_orders(self) -> List[dict]:
        return [order.to_dict() for order in self.repository.list_all()]

    def get_by_invoice(self, invoice_number: str) -> Optional[dict]:
        order = self.repository.get_by_invoice_number(invoice_number)
        return order.to_dict() if order else None

    def create_order(self, customer_name: str, items: List[Dict[str, Any]], status: str = 'paid', payment_status: str = 'paid') -> Order:
        if not customer_name.strip():
            raise ValueError('Customer name is required for order creation')

        customer = self.customer_service.get_by_name(customer_name)
        if not customer:
            customer = self.customer_service.create_customer(customer_name)

        invoice_number = self._generate_invoice_number()
        order = Order(
            invoice_number=invoice_number,
            customer=customer,
            subtotal=0.0,
            tax=0.0,
            total=0.0,
            status=status,
            payment_status=payment_status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.session.add(order)
        self.session.flush()

        subtotal = 0.0
        for item_data in items:
            name = str(item_data.get('name') or '').strip()
            quantity = float(item_data.get('qty') or item_data.get('quantity') or 0.0)
            product = self.inventory_service.resolve_product(name)
            explicit_price = item_data.get('price', item_data.get('unit_price'))
            if product:
                unit_price = float(product.price)
            elif explicit_price is not None:
                unit_price = float(explicit_price)
            else:
                unit_price = 0.0
            line_total = round(unit_price * quantity, 2)
            subtotal += line_total

            order_item = OrderItem(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
            self.session.add(order_item)

            if product:
                self.inventory_service.adjust_stock(product.name, -quantity)

        order.subtotal = subtotal
        order.tax = 0.0
        order.total = subtotal
        updated = self.repository.update(order)
        self.customer_service.update_stats(customer, order.total)
        index_order_embedding(self.session, updated)
        return updated

    def update_order_status(self, invoice_number: str, status: str) -> Optional[Order]:
        order = self.repository.get_by_invoice_number(invoice_number)
        if not order:
            return None
        order.status = status
        return self.repository.update(order)

    def _generate_invoice_number(self) -> str:
        return f'INV-{self.repository.get_max_invoice_sequence() + 1}'
