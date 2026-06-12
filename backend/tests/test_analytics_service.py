from backend.services.analytics_service import AnalyticsService
from backend.services.customer_service import CustomerService
from backend.services.inventory_service import InventoryService
from backend.services.order_service import OrderService


def test_analytics_service_summary(db_session):
    inventory_service = InventoryService(db_session)
    customer_service = CustomerService(db_session)
    order_service = OrderService(db_session)
    analytics_service = AnalyticsService(db_session)

    inventory_service.create_or_update_product(
        name='Matches',
        sku='MAT001',
        price=10.0,
        qty=100,
        unit='pcs',
    )
    inventory_service.create_or_update_product(
        name='Soap',
        sku='SOAP01',
        price=5.0,
        qty=50,
        unit='pcs',
    )

    customer_service.create_customer('Alice')
    customer_service.create_customer('Bob')

    order_service.create_order(
        customer_name='Alice',
        items=[{'name': 'Matches', 'qty': 5}],
        status='paid',
        payment_status='paid',
    )
    order_service.create_order(
        customer_name='Alice',
        items=[{'name': 'Soap', 'qty': 2}],
        status='paid',
        payment_status='paid',
    )
    order_service.create_order(
        customer_name='Bob',
        items=[{'name': 'Soap', 'qty': 1}],
        status='paid',
        payment_status='paid',
    )

    analytics = analytics_service.build_analytics_report()

    assert analytics['revenue']['yearly'][0]['total'] == 65.0
    assert analytics['products']['best_sellers'][0]['name'] == 'Matches'
    assert any(customer['name'] == 'Alice' for customer in analytics['customers']['repeat_customers'])
    assert analytics['inventory']['low_stock_count'] == 0
