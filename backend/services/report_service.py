from typing import Dict

from backend.storage.database import get_db_session
from backend.services.customer_service import CustomerService
from backend.services.inventory_service import InventoryService
from backend.services.order_service import OrderService


class ReportService:
    def __init__(self, session):
        self.session = session
        self.inventory_service = InventoryService(session)
        self.customer_service = CustomerService(session)
        self.order_service = OrderService(session)

    def build_dashboard_state(self) -> Dict[str, object]:
        products = self.inventory_service.list_products()
        orders = self.order_service.list_orders()
        customers = self.customer_service.list_customers()
        low_stock = self.inventory_service.get_low_stock_products()

        revenue = sum(order['total'] for order in orders if order['status'] == 'paid')
        return {
            'inventory': products,
            'orders': orders,
            'customers': customers,
            'activity': [],
            'low_stock_count': len(low_stock),
            'low_stock_items': [p for p in low_stock[:5]],
            'revenue': revenue,
        }
