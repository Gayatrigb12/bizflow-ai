from backend.services.customer_service import CustomerService
from backend.services.inventory_service import InventoryService
from backend.services.order_service import OrderService


def test_create_and_update_product(db_session):
    inventory_service = InventoryService(db_session)
    product = inventory_service.create_or_update_product(
        name='Rice',
        sku='RIC001',
        price=50.0,
        qty=20,
        unit='kg',
    )

    assert product.name == 'Rice'
    assert product.quantity == 20
    assert product.price == 50.0

    updated = inventory_service.create_or_update_product(
        name='Rice',
        sku='RIC001',
        price=55.0,
        qty=5,
        unit='kg',
    )

    assert updated.quantity == 25
    assert updated.price == 55.0


def test_customer_creation_and_order(db_session):
    customer_service = CustomerService(db_session)
    order_service = OrderService(db_session)
    inventory_service = InventoryService(db_session)

    inventory_service.create_or_update_product(
        name='Wheat',
        sku='WHT001',
        price=40.0,
        qty=100,
        unit='kg',
    )

    customer = customer_service.create_customer('Suresh', phone='9876543210')
    order = order_service.create_order(
        customer_name='Suresh',
        items=[{'name': 'Wheat', 'qty': 10}],
        status='paid',
        payment_status='paid',
    )

    assert order.invoice_number.startswith('INV-')
    assert order.total == 400.0
    assert customer.total_spent == 400.0
    assert customer.order_count == 1

    product = inventory_service.find_by_name('Wheat')
    assert product.quantity == 90
