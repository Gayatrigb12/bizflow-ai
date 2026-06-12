from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from sqlalchemy import select

from backend.storage.models import Customer, OrderItem, Product
from backend.storage.repositories.customer_repository import CustomerRepository
from backend.storage.repositories.inventory_repository import InventoryRepository
from backend.storage.repositories.order_repository import OrderRepository


class AnalyticsService:
    def __init__(self, session):
        self.session = session
        self.order_repository = OrderRepository(session)
        self.inventory_repository = InventoryRepository(session)
        self.customer_repository = CustomerRepository(session)

    def build_analytics_report(self) -> Dict[str, object]:
        return {
            'revenue': self._build_revenue_summary(),
            'inventory': self._build_inventory_summary(),
            'customers': self._build_customer_summary(),
            'products': self._build_product_summary(),
        }

    def _build_revenue_summary(self) -> Dict[str, List[Dict[str, object]]]:
        paid_orders = [order for order in self.order_repository.list_all() if order.status == 'paid']
        daily_totals: dict[str, float] = defaultdict(float)
        weekly_totals: dict[str, float] = defaultdict(float)
        monthly_totals: dict[str, float] = defaultdict(float)
        yearly_totals: dict[str, float] = defaultdict(float)

        for order in paid_orders:
            if not order.created_at:
                continue

            timestamp = order.created_at
            total = float(order.total or 0.0)
            daily_totals[timestamp.date().isoformat()] += total
            week = timestamp.isocalendar()
            weekly_totals[f'{week.year}-W{week.week:02d}'] += total
            monthly_totals[f'{timestamp.year}-{timestamp.month:02d}'] += total
            yearly_totals[f'{timestamp.year}'] += total

        return {
            'daily': self._format_period_totals(daily_totals),
            'weekly': self._format_period_totals(weekly_totals),
            'monthly': self._format_period_totals(monthly_totals),
            'yearly': self._format_period_totals(yearly_totals),
        }

    def _build_inventory_summary(self) -> Dict[str, object]:
        low_stock_products = [product.to_dict() for product in self.inventory_repository.list_low_stock()]
        product_sales = self._build_product_sales()

        fast_moving = sorted(product_sales, key=lambda item: item['quantity_sold'], reverse=True)[:5]
        slow_moving = sorted(product_sales, key=lambda item: item['quantity_sold'])[:5]

        return {
            'low_stock_count': len(low_stock_products),
            'low_stock_products': low_stock_products,
            'fast_moving_products': fast_moving,
            'slow_moving_products': slow_moving,
        }

    def _build_customer_summary(self) -> Dict[str, List[Dict[str, object]]]:
        customers = self.customer_repository.list_all()
        top_customers = sorted(customers, key=lambda item: float(item.total_spent or 0.0), reverse=True)[:5]
        new_customers = sorted(customers, key=lambda item: item.created_at or datetime.min, reverse=True)[:5]
        repeat_customers = sorted(
            [customer for customer in customers if (customer.order_count or 0) > 1],
            key=lambda item: item.order_count,
            reverse=True,
        )[:5]

        return {
            'top_customers': [customer.to_dict() for customer in top_customers],
            'new_customers': [customer.to_dict() for customer in new_customers],
            'repeat_customers': [customer.to_dict() for customer in repeat_customers],
        }

    def _build_product_summary(self) -> Dict[str, List[Dict[str, object]]]:
        product_sales = self._build_product_sales()
        best_sellers = sorted(product_sales, key=lambda item: item['quantity_sold'], reverse=True)[:5]
        least_selling = sorted(product_sales, key=lambda item: item['quantity_sold'])[:5]

        return {
            'best_sellers': best_sellers,
            'least_selling_products': least_selling,
        }

    def _build_product_sales(self) -> List[Dict[str, object]]:
        products = self.inventory_repository.list_all()
        sales_summary = {
            product.id: {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'price': float(product.price or 0.0),
                'quantity': float(product.quantity or 0.0),
                'quantity_sold': 0.0,
                'revenue': 0.0,
            }
            for product in products
        }

        items = self.session.execute(select(OrderItem)).scalars().all()
        for item in items:
            summary = sales_summary.get(item.product_id)
            if not summary:
                continue
            summary['quantity_sold'] += float(item.quantity or 0.0)
            summary['revenue'] += float(item.line_total or 0.0)

        return list(sales_summary.values())

    @staticmethod
    def _format_period_totals(period_totals: dict[str, float]) -> List[Dict[str, object]]:
        return [
            {'period': key, 'total': round(value, 2)}
            for key, value in sorted(period_totals.items())
        ]
