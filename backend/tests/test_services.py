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


def test_resolve_product_with_quantity_prefix(db_session):
    inventory_service = InventoryService(db_session)
    inventory_service.create_or_update_product(
        name='Apple',
        sku='APL001',
        price=70.0,
        qty=100,
        unit='kg',
    )
    product = inventory_service.resolve_product('10kg Apple')
    assert product is not None
    assert product.name == 'Apple'


def test_create_order_returns_total_in_action(db_session):
    from backend.ai.action_executor import execute_action

    inventory_service = InventoryService(db_session)
    inventory_service.create_or_update_product(
        name='Apple',
        sku='APL001',
        price=70.0,
        qty=100,
        unit='kg',
    )
    customer_service = CustomerService(db_session)
    customer_service.create_customer('Priyanka')

    result = execute_action(
        db_session,
        {
            'type': 'create_order',
            'customer': 'Priyanka',
            'items': [{'name': 'Apple', 'qty': 10}],
        },
        actor='test',
    )
    assert result['invoice_number'].startswith('INV-')
    assert result['total'] == 700.0
    assert result['customer'] == 'Priyanka'


def test_generate_invoice_number_uses_max_sequence(db_session):
    from backend.storage.models import Order
    from datetime import datetime

    customer_service = CustomerService(db_session)
    customer = customer_service.create_customer('Invoice Test Customer')
    order_service = OrderService(db_session)
    db_session.add_all([
        Order(
            invoice_number='INV-1014',
            customer_id=customer.id,
            subtotal=0,
            tax=0,
            total=0,
            status='paid',
            payment_status='paid',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        Order(
            invoice_number='INV-1016',
            customer_id=customer.id,
            subtotal=0,
            tax=0,
            total=0,
            status='paid',
            payment_status='paid',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
    ])
    db_session.flush()

    assert order_service._generate_invoice_number() == 'INV-1017'
