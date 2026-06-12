import json
import os
from pathlib import Path

from backend.storage.database import engine
from backend.storage.models import Base, Customer, Order, OrderItem, Product, ActivityLog
from sqlalchemy.orm import Session

SOURCE_FILE = Path(__file__).resolve().parents[2] / 'data' / 'store.json'


def load_legacy_data():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f'Legacy store file not found: {SOURCE_FILE}')

    with open(SOURCE_FILE, 'r', encoding='utf-8') as file:
        return json.load(file)


def migrate():
    Base.metadata.create_all(engine)
    legacy = load_legacy_data()

    with Session(engine) as session:
        inventory = legacy.get('inventory', [])
        for item in inventory:
            session.add(Product(
                sku=str(item.get('sku') or item.get('name', '')[:8]).strip(),
                name=str(item.get('name') or '').strip(),
                description=str(item.get('description') or ''),
                unit=str(item.get('unit') or 'pcs'),
                price=float(item.get('price') or 0.0),
                quantity=float(item.get('qty') or item.get('quantity') or 0.0),
                low_stock_threshold=float(item.get('low_stock_threshold') or 10.0),
            ))

        customers = legacy.get('customers', [])
        for customer in customers:
            session.add(Customer(
                name=str(customer.get('name') or '').strip(),
                phone=str(customer.get('phone') or ''),
                email=str(customer.get('email') or ''),
                address=str(customer.get('address') or ''),
                total_spent=float(customer.get('total_spent') or customer.get('total_spent', 0.0)),
                order_count=int(customer.get('orders') or customer.get('order_count') or 0),
            ))

        orders = legacy.get('orders', [])
        for order_data in orders:
            customer_name = str(order_data.get('customer') or 'Walk-in').strip()
            customer = session.query(Customer).filter(Customer.name.ilike(customer_name)).first()
            if not customer:
                customer = Customer(name=customer_name)
                session.add(customer)
                session.flush()

            order = Order(
                invoice_number=str(order_data.get('id') or ''),
                customer=customer,
                subtotal=float(order_data.get('total') or 0.0),
                tax=0.0,
                total=float(order_data.get('total') or 0.0),
                status=str(order_data.get('status') or 'paid'),
                payment_status='paid',
            )
            session.add(order)
            session.flush()

            for item in order_data.get('items', []):
                product_name = str(item.get('name') or '').strip()
                product = session.query(Product).filter(Product.name.ilike(product_name)).first()
                session.add(OrderItem(
                    order=order,
                    product=product,
                    quantity=float(item.get('qty') or item.get('quantity') or 0.0),
                    unit_price=float(item.get('price') or 0.0),
                    line_total=float(item.get('subtotal') or 0.0),
                ))

        activity = legacy.get('activity', [])
        for entry in activity:
            session.add(ActivityLog(
                action_type=str(entry.get('type') or ''),
                description=str(entry.get('text') or ''),
                actor=str(entry.get('value') or ''),
            ))

        session.commit()

    print('Legacy data migrated successfully.')


if __name__ == '__main__':
    migrate()
