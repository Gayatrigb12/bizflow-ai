from backend.ai.action_validator import ActionValidator
from backend.services.inventory_service import InventoryService
from backend.services.pending_action_service import PendingActionService


def test_action_validator_requires_approval_for_delete_product(db_session):
    validator = ActionValidator(session=db_session, inventory_service=InventoryService(db_session))
    result = validator.validate({'type': 'delete_product', 'name': 'Sugar'})

    assert result.valid
    assert result.requires_approval
    assert result.errors == []


def test_pending_action_can_be_created_and_approved(db_session):
    inventory_service = InventoryService(db_session)
    inventory_service.create_or_update_product(
        name='Sugar',
        sku='SUG001',
        price=30.0,
        qty=50,
        unit='kg',
    )

    pending_service = PendingActionService(db_session)
    pending = pending_service.create_pending_action(
        actions=[{'type': 'delete_product', 'name': 'Sugar'}],
        reply='Please remove Sugar',
        requested_by='AI',
    )

    assert pending.status == 'pending'
    assert pending.requested_by == 'AI'
    assert pending.payload['actions'][0]['type'] == 'delete_product'

    approved = pending_service.approve_pending_action(pending.id, reviewer='admin', review_comment='Approved')
    assert approved['pending_action_id'] == pending.id
    assert approved['executed'][0]['type'] == 'delete_product'
    assert approved['executed'][0].get('error') is None

    assert inventory_service.find_by_name('Sugar') is None
