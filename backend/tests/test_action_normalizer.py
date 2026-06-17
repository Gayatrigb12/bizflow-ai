from backend.ai.action_normalizer import normalize_action, normalize_actions
from backend.ai.action_validator import ActionValidator


def test_normalize_update_inventory_to_add_product():
    action = {
        'type': 'update_inventory',
        'name': 'Rice',
        'price': 60,
        'quantity': 100,
        'unit': 'kg',
    }
    normalized = normalize_action(action)
    assert normalized['type'] == 'add_product'
    assert normalized['name'] == 'Rice'
    assert normalized['price'] == 60
    assert normalized['qty'] == 100
    assert normalized['unit'] == 'kg'


def test_normalize_update_inventory_to_update_stock():
    action = {'type': 'update_inventory', 'name': 'Rice', 'qty_change': 10}
    normalized = normalize_action(action)
    assert normalized['type'] == 'update_stock'
    assert normalized['qty_change'] == 10


def test_normalize_create_customer_alias():
    action = {'type': 'create_customer', 'customer_name': 'Tripura'}
    normalized = normalize_action(action)
    assert normalized['type'] == 'add_customer'
    assert normalized['name'] == 'Tripura'


def test_normalize_create_invoice_to_create_order():
    action = {
        'type': 'create_invoice',
        'customer_name': 'Rahul',
        'items': [{'product': 'Rice', 'quantity': 3}],
    }
    normalized = normalize_action(action)
    assert normalized['type'] == 'create_order'
    assert normalized['customer'] == 'Rahul'
    assert normalized['items'] == [{'name': 'Rice', 'qty': 3}]


def test_normalize_order_item_with_embedded_quantity():
    action = normalize_action({
        'type': 'create_order',
        'customer': 'Priyanka',
        'items': [{'name': '10kg Apple'}],
    })
    assert action['items'] == [{'name': 'Apple', 'qty': 10.0}]


def test_normalized_add_product_passes_validation(db_session):
    validator = ActionValidator(session=db_session)
    action = normalize_action({
        'type': 'update_inventory',
        'name': 'Rice',
        'price': 60,
        'qty': 100,
    })
    result = validator.validate(action)
    assert result.valid
    assert result.errors == []


def test_normalize_actions_list():
    actions = normalize_actions([
        {'type': 'set_stock', 'name': 'Sugar', 'price': 40, 'qty': 20},
        {'type': 'adjust_stock', 'name': 'Sugar', 'qty_change': -2},
    ])
    assert actions[0]['type'] == 'add_product'
    assert actions[1]['type'] == 'update_stock'
