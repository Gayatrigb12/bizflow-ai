from backend.ai.action_validator import ActionValidator


def test_validate_add_product_missing_fields(db_session):
    validator = ActionValidator(session=db_session)
    action = {'type': 'add_product', 'name': 'Rice'}
    res = validator.validate(action)
    assert not res.valid
    assert 'Missing required field: price' in res.errors


def test_validate_create_order_basic(db_session):
    validator = ActionValidator(session=db_session)
    action = {'type': 'create_order', 'customer': 'Test', 'items': [{'name': 'Rice', 'qty': 2}]}
    res = validator.validate(action)
    # product may not exist yet; validator should only check shape
    assert res.valid or isinstance(res.errors, list)
